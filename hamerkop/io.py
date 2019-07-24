# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import csv
import io
import logging
import re
import zipfile

from .core import Document, DocType, Entity, EntityType, Link, LinkType, Mention, GeoContext, OrgContext, PerContext
from .lang import NgramLangDetector
from .string import String
from .utilities import InProcessIncremental

logger = logging.getLogger(__name__)


class InputReader:
    def __init__(self, fp, id_assigner=None, lang_detector=None, preparer=None):
        self.reader = read_conll(fp)
        if preparer is None:
            if id_assigner is None:
                id_assigner = InProcessIncremental()
            if lang_detector is None:
                lang_detector = NgramLangDetector()
            self.preparer = DocumentPreparer(id_assigner, lang_detector)
        else:
            self.preparer = preparer

    def __iter__(self):
        return self

    def __next__(self):
        document = self.preparer.process(next(self.reader))
        while document is None:
            document = self.preparer.process(next(self.reader))
        return document


Row = collections.namedtuple('Row', 'token tag doc_id offsets sent_id')


class CoNLLReaderException(Exception):
    """An error occurred when reading and parsing a CoNLL file."""


def read_conll(fp):
    """
    Generator that returns a list of Row tuples for each document
    :param fp: handle to CoNLL tsv file with columns: token tag token doc_id start stop sentence
    :return: list of Row tuples
    """
    reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
    first_row = next(reader)
    if not first_row:
        raise CoNLLReaderException("csv reader cannot read first line of {}".format(fp.name))
    if first_row[0].lower() in ['token', 'tok']:
        raise CoNLLReaderException("Reader does not handle file with header: {}".format(fp.name))
    fp.seek(0)

    # take token from conll-full file
    token_index = 2
    tag_index = 1
    doc_id_index = 3
    offsets_indexes = (4, 5)
    sent_id_index = 6

    rows = []
    current_doc_id = None
    for row in reader:
        if len(row) < 6:
            # sentence breaks are ignored
            continue

        if not row[tag_index]:
            raise RuntimeError("Bad conll format data: {}".format(row))

        if current_doc_id is None:
            current_doc_id = row[doc_id_index]

        if row[doc_id_index] != current_doc_id:
            yield rows
            rows = []
            current_doc_id = row[doc_id_index]

        start = int(row[offsets_indexes[0]])
        stop = int(row[offsets_indexes[1]])
        sent_id = int(row[sent_id_index].split('-')[1])
        rows.append(Row(row[token_index], row[tag_index], row[doc_id_index], (start, stop), sent_id))
    yield rows


class DocumentPreparer(object):
    """
    Prepare a document from a list of rows extracted from tagged conll file
    This does not check for conditions like B-PER I-ORG.
    This passes all tag types so B-DOG will end up as a mention.
    """
    def __init__(self, id_assigner, lang_detector):
        """
        :param id_assigner: Identifier
        :param lang_detector: LangDetector
        """
        self.id_assigner = id_assigner
        self.lang_detector = lang_detector

    def process(self, rows):
        """
        Turn a list of rows into entity mentions
        :param rows: list of Row namedtuples
        :return: Document or None if no mentions
        """
        tokens = []
        sentences = collections.defaultdict(list)
        token_index = token_start = 0
        mentions = []
        mention_rows = []
        in_mention = False
        for row in rows:
            if in_mention:
                if row.tag[0] != 'I':
                    in_mention = False
                    mentions.append(self._extract(mention_rows, token_start))
                    mention_rows = []
                else:
                    mention_rows.append(row)
            if row.tag[0] == 'B':
                in_mention = True
                token_start = token_index
                mention_rows.append(row)

            tokens.append(row.token)
            sentences[row.sent_id].append(row.token)
            token_index += 1

        if in_mention:
            mentions.append(self._extract(mention_rows, token_start))

        if mentions:
            filename = mentions[0].doc_id
            doc_type = DocType.detect(filename)
            lang = self.lang_detector.detect(filename, tokens)
            sents = [sentences[index] for index in sorted(sentences.keys())]
            return Document(mentions, doc_type, lang, tokens, sents)

    def _extract(self, rows, token_start):
        first_row = rows.pop(0)
        name = first_row.token
        ch_start = first_row.offsets[0]
        ch_stop = first_row.offsets[1]
        token_stop = token_start + 1
        doc_id = first_row.doc_id
        type = first_row.tag[2:]
        for row in rows:
            name = ' '.join((name, row.token))
            ch_stop = row.offsets[1]
            token_stop += 1
        token_offsets = (token_start, token_stop)
        mention = Mention(name, doc_id, (ch_start, ch_stop), token_offsets, type)
        self.id_assigner.assign(mention)
        return mention


class DocumentPreparerUsingGroundTruth(object):
    """
    Prepare a document from a list of rows extracted from tagged conll file plus ground truth
    """
    def __init__(self, id_assigner, lang_detector, ground_truth):
        """
        :param id_assigner: Identifier
        :param lang_detector: LangDetector
        :param ground_truth: output of OutputReader (doc -> offset -> Link)
        """
        self.id_assigner = id_assigner
        self.lang_detector = lang_detector
        self.ground_truth = self._prepare_ground_truth(ground_truth)

    def process(self, rows):
        """
        Turn a list of rows into entity mentions
        :param rows: list of Row namedtuples
        :return: Document or None if no mentions
        """
        tokens = []
        sentences = collections.defaultdict(list)
        token_index = token_start = 0
        mentions = []
        mention_rows = []
        in_mention = False
        doc_id = rows[0].doc_id
        if doc_id not in self.ground_truth:
            return None
        gt = self.ground_truth[doc_id]
        tag = None
        for row in rows:
            if in_mention:
                mention_rows.append(row)
                if row.offsets[1] == tag['end_offset']:
                    mentions.append(self._extract(mention_rows, token_start, tag['type']))
                    in_mention = False
                    tag = None
                    mention_rows = []

            if row.offsets[0] in gt:
                # start of a new tag
                tag = gt[row.offsets[0]]
                in_mention = True
                token_start = token_index
                mention_rows.append(row)
                if row.offsets[1] == tag['end_offset']:
                    # single token tag
                    mentions.append(self._extract(mention_rows, token_start, tag['type']))
                    in_mention = False
                    tag = None
                    mention_rows = []

            tokens.append(row.token)
            sentences[row.sent_id].append(row.token)
            token_index += 1

        if mentions:
            filename = mentions[0].doc_id
            doc_type = DocType.detect(filename)
            lang = self.lang_detector.detect(filename, tokens)
            sents = [sentences[index] for index in sorted(sentences.keys())]
            return Document(mentions, doc_type, lang, tokens, sents)

    def _extract(self, rows, token_start, type):
        first_row = rows.pop(0)
        name = first_row.token
        ch_start = first_row.offsets[0]
        ch_stop = first_row.offsets[1]
        token_stop = token_start + 1
        doc_id = first_row.doc_id
        for row in rows:
            name = ' '.join((name, row.token))
            ch_stop = row.offsets[1]
            token_stop += 1
        token_offsets = (token_start, token_stop)
        mention = Mention(name, doc_id, (ch_start, ch_stop), token_offsets, type)
        self.id_assigner.assign(mention)
        return mention

    @staticmethod
    def _prepare_ground_truth(gt):
        new_gt = {}
        for doc in gt:
            new_gt[doc] = {}
            for offsets in gt[doc]:
                new_gt[doc][offsets[0]] = {'end_offset': offsets[1], 'type': gt[doc][offsets].entity_type}
        return new_gt


class EvalTabFormat:
    """Columns of LoReHLT submission format"""
    SYSTEM = 0
    MENTION_ID = 1
    MENTION_TEXT = 2
    DOC_AND_OFFSETS = 3
    KB_ID = 4
    ENTITY_TYPE = 5
    MENTION_TYPE = 6
    CONFIDENCE = 7


class OutputWriter:
    """
    Writes a file that conforms to the LoReHLT submission format

    Sets the KB_ID to NIL for mentions without a match.
    NIL clustering is not included.
    """
    def __init__(self, fp, system, prob=0.1):
        """
        :param fp: handle to a file open for writing
        :param system: name of system
        :param prob: confidence value of data
        """
        self.fp = fp
        self.system = system
        self.prob = prob

    def write(self, document):
        for chain in document.mention_chains:
            if chain.entity is None:
                entity = 'NIL'
            else:
                entity = chain.entity.id
            for mention in chain.mentions:
                doc_info = "{}:{}-{}".format(mention.doc_id, *mention.offsets)
                line = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    self.system, mention.id, mention.original_string, doc_info,
                    entity, mention.type, 'NAM', self.prob)
                self.fp.write(line)


class OutputReader:
    """
    Reads the LoReHLT submission format for using ground truth.

    The data is stored in a dict as doc -> {offsets -> link}
    """
    @staticmethod
    def read(fp):
        """
        :param fp: handle to open file for reading
        :return: dictionary of ground truth
        """
        data = collections.defaultdict(dict)
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        first_row = next(reader)
        assert first_row[EvalTabFormat.SYSTEM] == 'system_run_id'
        for row in reader:
            name = row[EvalTabFormat.MENTION_TEXT]
            doc_id = row[EvalTabFormat.DOC_AND_OFFSETS].split(':')[0]
            offset_strings = row[EvalTabFormat.DOC_AND_OFFSETS].split(':')[1].split('-')
            offsets = tuple(map(int, offset_strings))
            if LinkType.NIL in row[EvalTabFormat.KB_ID]:
                link_type = LinkType.NIL
            else:
                link_type = LinkType.LINK
            links = []
            cluster_id = None
            if link_type == LinkType.LINK:
                links = row[EvalTabFormat.KB_ID].split('|')
            else:
                cluster_id = row[EvalTabFormat.KB_ID]
            data[doc_id][offsets] = Link(row[EvalTabFormat.ENTITY_TYPE], link_type, links, cluster_id, name)
        return data


class EntityCreator:
    """
    Generates an Entity from a row from TSV file
    """
    # LoReHLT Knowledge Base columns
    ORIGIN = 0
    ENTITY_TYPE = 1
    ENTITY_ID = 2
    NAME = 3
    ASCIINAME = 4
    LATITUDE = 5
    LONGITUDE = 6
    FEATURE_CLASS = 7
    FEATURE_CLASS_NAME = 8
    FEATURE_CODE = 9
    FEATURE_CODE_NAME = 10
    FEATURE_CODE_DESCRIPTION = 11
    COUNTRY_CODE = 12
    COUNTRY_CODE_NAME = 13
    CC2 = 14
    ADMIN1_CODE = 15
    ADMIN1_CODE_NAME = 16
    ADMIN2_CODE = 17
    ADMIN2_CODE_NAME = 18
    ADMIN3_CODE = 19
    ADMIN4_CODE = 20
    POPULATION = 21
    ELEVATION = 22
    DEM = 23
    TIMEZONE = 24
    MODIFICATION_DATE = 25
    PER_GPE_LOC_OF_ASSOCIATION = 26
    PER_TITLE_OR_POSITION = 27
    PER_ORG_OF_ASSOCIATION = 28
    PER_ROLE_IN_INCIDENT = 29
    PER_YEAR_OF_BIRTH = 30
    PER_YEAR_OF_DEATH = 31
    PER_GENDER = 32
    PER_FAMILY_MEMBER = 33
    NOTE = 34
    AIM = 35
    ORG_DATE_ESTABLISHED = 36
    DATE_ESTABLISHED_NOTE = 37
    ORG_WEBSITE = 38
    ORG_GPE_LOC_OF_ASSOCIATION = 39
    ORG_MEMBERS_EMPLOYEES_PER = 40
    ORG_PARENT_ORG = 41
    EXECUTIVE_BOARD_MEMBERS = 42
    JURISDICTION = 43
    TRUSTEESHIP_COUNCIL = 44
    NATIONAL_SOCIETIES = 45
    EXTERNAL_LINK = 46

    ENTITY_KEYS = [ENTITY_ID, ENTITY_TYPE, NAME, ORIGIN, EXTERNAL_LINK]

    @classmethod
    def create(cls, row, include_context=False):
        data = [row[key] for key in cls.ENTITY_KEYS]
        data[-1] = [] if data[-1] == '' else data[-1].split('|')
        entity = Entity(*data)
        if include_context:
            if entity.type == EntityType.PER:
                context = cls._create_per_context(row)
            elif entity.type == EntityType.ORG:
                context = cls._create_org_context(row)
            else:
                context = cls._create_geo_context(row)
            entity.context = context
        return entity

    @classmethod
    def _create_per_context(cls, row):
        locations = row[cls.PER_GPE_LOC_OF_ASSOCIATION].split('|')
        return PerContext(
            location=locations[0] if locations else None,
            titles=row[cls.PER_TITLE_OR_POSITION].split('|'),
            organizations=row[cls.PER_ORG_OF_ASSOCIATION].split('|')
        )

    @classmethod
    def _create_org_context(cls, row):
        locations = row[cls.ORG_GPE_LOC_OF_ASSOCIATION].split('|')
        return OrgContext(
            location=locations[0] if locations else None
        )

    @classmethod
    def _create_geo_context(cls, row):
        country = row[cls.COUNTRY_CODE] if row[cls.COUNTRY_CODE] else None
        return GeoContext(
            type=row[cls.FEATURE_CODE_NAME],
            country=country,
            latitude=cls._float(row[cls.LATITUDE]),
            longitude=cls._float(row[cls.LONGITUDE]),
            population=cls._int(row[cls.POPULATION])
        )

    @staticmethod
    def _float(value):
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _int(value):
        try:
            return int(value)
        except ValueError:
            return None


class EntityLoader:
    """
    Load entities from TSV files
    """
    def __init__(self, entities_fp, alt_names_fp, entity_filter=None, name_filter=None, verbose=False):
        """
        :param entities_fp: handle for reading the entities file
        :param alt_names_fp: handle for reading the alternate names file
        :param entity_filter: EntityFilter
        :param name_filter: NameFilter
        :param verbose: Whether to write entity loading progress to STDOUT
        """
        self.entities_fp = entities_fp
        self.alt_names_fp = alt_names_fp
        self.entity_filter = entity_filter
        self.name_filter = name_filter
        self.verbose = verbose

    def load(self):
        entities = self._load_entities()
        self._load_alt_names(entities)
        return entities

    def _load_entities(self):
        entity_count = 0
        entities = {}
        reader = csv.reader(self.entities_fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            if self.entity_filter and not self.entity_filter.filter(row):
                continue
            entity = EntityCreator.create(row, True)
            entities[entity.id] = entity
            entity_count += 1
            if self.verbose and entity_count % 10000 == 0:
                print('KB entity loading: {0: >10,}'.format(entity_count), end='\r')
        logger.info('Loaded {} entities'.format(len(entities)))
        if self.verbose:
            print('KB entity loading complete: {0: >10,}'.format(entity_count))
        return entities

    def _load_alt_names(self, entities):
        name_count = 0
        reader = csv.reader(self.alt_names_fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            entity_id = row[0]
            alt_name = row[1]
            if entity_id in entities:
                if self.name_filter and not self.name_filter.filter(alt_name):
                    continue
                entities[entity_id].names.add(alt_name)
                name_count += 1
                if self.verbose and name_count % 10000 == 0:
                    print('KB name loading: {0: >10,}'.format(name_count), end='\r')
        logger.info('Loaded {} alternate names'.format(name_count))
        if self.verbose:
            print('KB name loading complete: {0: >10,}'.format(name_count))


class EntityFilter(abc.ABC):
    """
    Remove entities before populating a KB

    The LoReHLT KB has ~10 million entities.
    The vast majority of these entities are unrelated to the evaluation and present a scaling challenge.
    We use some heuristics to prune the list of possible entities in the KB.
    """
    @abc.abstractmethod
    def filter(self, row):
        """
        Filter the entities to only include ones that might be relevant
        :param row: list from the entities CSV file
        :return: True = include, False = exclude (None = delays decision for another filter in cascade)
        """
        pass


class CascadeEntityFilter(EntityFilter):
    """Run a series of filters"""
    def __init__(self, filters):
        self.filters = filters

    def filter(self, row):
        for f in self.filters:
            result = f.filter(row)
            if result is None:
                continue
            return result
        # no filter wanted to keep it
        return False


class EntityOriginFilter(EntityFilter):
    """Keep entities from particular origins"""
    def __init__(self, *origins):
        """
        :param origins: data sources for entities ('WLL', 'APB', 'AUG')
        """
        self.origins = origins

    def filter(self, row):
        if row[EntityCreator.ORIGIN][:3] in self.origins:
            return True


class EntityLinkFilter(EntityFilter):
    """Keep entities with external links"""
    def filter(self, row):
        if row[EntityCreator.EXTERNAL_LINK]:
            return True


class EntityCountryFilter(EntityFilter):
    """Keep entities with particular countries"""
    def __init__(self, *cc):
        """
        :param cc: 2 letter country codes
        """
        self.cc = {code.upper() for code in cc}

    def filter(self, row):
        if row[EntityCreator.COUNTRY_CODE] in self.cc:
            return True


class NameFilter(abc.ABC):
    """
    Remove names before populating a KB

    The LoReHLT KB has ~23 million names. Many of these are in languages unrelated to the evaluation.
    """
    @abc.abstractmethod
    def filter(self, name):
        """
        Filter the name
        :param name: name string
        :return: True = include, False = exclude (None = delays decision for another filter in a cascade)
        """
        pass


class CascadeNameFilter(NameFilter):
    """Run a series of filters"""
    def __init__(self, filters):
        self.filters = filters

    def filter(self, name):
        for f in self.filters:
            result = f.filter(name)
            if result is None:
                continue
            return result
        # no filter wanted to keep it
        return False


class ScriptBasedNameFilter:
    """
    Filter alternate names when loading the kb by script.

    English is always included. Other scripts can be included.
    """
    GEEZ = "ge'ez"
    ARABIC = "arabic"
    SINHALA = "sinhala"
    ODIA = "odia"

    REGEXES = {
        GEEZ: re.compile(r'^[\u1200-\u137F]+$'),  # does not include supplement or extended
        ARABIC: re.compile(r'^[\u0600-\u06FF]+$'),  # does not include supplement or extended
        SINHALA: re.compile(r'^[\u0D80-\u0DFF]+$'),
        ODIA: re.compile(r'^[\u0B00-\u0B7F]+$'),
    }

    def __init__(self, *scripts):
        self.scripts = [x.lower() for x in scripts]

    def filter(self, name):
        s = String.replace_unicode_punct(name)
        s = String.replace_punct(s)
        if self.is_english(s):
            return True
        for script in self.scripts:
            if re.match(self.REGEXES[script], s):
                return True
        return False

    @staticmethod
    def is_english(name):
        return all([ord(c) <= 127 for c in name])


class LanguageBasedNameFilter:
    """
    Uses Geonames to determine the language of the name string
    """
    LANG = 2
    NAME = 3
    ENGLISH = 'en'
    ALT_NAMES_FILE = 'alternateNamesV2.txt'

    def __init__(self, filename, lang):
        """
        :param filename: Path to alternateNamesV2.zip
        :param lang: 2 letter language code of the language of interest
        """
        self.names = {}
        self.langs = {self.ENGLISH, lang.lower()}
        with zipfile.ZipFile(filename, 'r') as zfp:
            with zfp.open(self.ALT_NAMES_FILE, 'r') as fp:
                reader = csv.reader(io.TextIOWrapper(fp), delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    lang = row[self.LANG]
                    name = row[self.NAME].lower()
                    # don't overwrite English as the language (for example, France is a name in en and fr)
                    if name in self.names and self.names[name] in self.langs:
                        continue
                    self.names[name] = lang
        self.langs.add('')  # many names have no language code and we'll allow them through in filter

    def filter(self, name):
        name = name.lower()
        if name in self.names and self.names[name] not in self.langs:
            return False
        return True
