# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import csv
import logging
import math
import os
import pickle
import re

from .core import Entity, EntityType, LinkType
from .string import String
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class KBException(Exception):
    """An error occurred when interacting with the KB."""


class KB(abc.ABC):
    """
    Knowledge base interface
    Provides methods for retrieving entities but not searching for them.
    See NameIndex for search methods.
    """

    @abc.abstractmethod
    def size(self):
        """
        Get the number of entities in the KB
        :return: int
        """
        pass

    @abc.abstractmethod
    def get_entity(self, entity_id):
        """
        Get an entity
        :param entity_id: string
        :return: Entity
        """
        pass

    @abc.abstractmethod
    def get_entities(self, entity_ids):
        """
        Get a list of entities
        :param entity_ids: list of entity ids
        :return: list
        """
        pass


class EntityCreator:
    """
    Generates an Entity from a row from CSV file
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

    @classmethod
    def create(cls, row, include_context=False):
        # TODO: not processing context yet
        keys = [cls.ENTITY_ID, cls.ENTITY_TYPE, cls.NAME, cls.ORIGIN, cls.LATITUDE,
                cls.LONGITUDE, cls.COUNTRY_CODE, cls.POPULATION, cls.EXTERNAL_LINK]
        data = [row[key] for key in keys]
        data[-1] = [] if data[-1] == '' else data[-1].split('|')
        data[4] = cls._float(data[4])
        data[5] = cls._float(data[5])
        data[6] = data[6] if data[6] else None
        data[7] = cls._int(data[7])
        entity = Entity(*data)
        return entity

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


class KBLoadingScorer:
    def __init__(self, kb, gt):
        self.kb = kb
        self.ids = self._prepare(gt)
        self.recall = 0
        self.missed = set()

    def score(self):
        in_kb_count = 0
        for entity_id in self.ids:
            if self.kb.get_entity(entity_id):
                in_kb_count += 1
            else:
                self.missed.add(entity_id)
        self.recall = in_kb_count / len(self.ids)

    def _prepare(self, gt):
        ids = set()
        for doc in gt:
            for link in gt[doc].values():
                if link.link_type == LinkType.LINK:
                    ids.update(link.links)
        return ids


class MemoryKB(KB):
    """
    KB backed by a python dictionary for smaller kbs.

    The dictionary is entity ID -> Entity object
    """
    CACHE_EXT = '.cache.pkl'

    def __init__(self, entities_fp, alt_names_fp, entity_filter=None, name_filter=None, verbose=False, cache=True):
        """
        :param entities_fp: handle for reading the entities file
        :param alt_names_fp: handle for reading the alternate names file
        :param entity_filter: EntityFilter
        :param name_filter: NameFilter
        :param verbose: Whether to write entity loading progress to STDOUT
        """
        self.entity_filter = entity_filter
        self.name_filter = name_filter
        self.verbose = verbose

        cache_path = entities_fp.name + self.CACHE_EXT
        if cache and os.path.exists(cache_path):
            if self.verbose:
                print("Loading entities from the cache")
            self._read_cache(cache_path)
        else:
            self.entities = self._load_entities(entities_fp)
            self._load_alt_names(alt_names_fp)
            if cache:
                self._write_cache(cache_path)

    def size(self):
        return len(self.entities)

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def get_entities(self, entity_ids):
        return [self.entities[x] for x in entity_ids if x in self.entities]

    def __iter__(self):
        for entity in self.entities.values():
            yield entity

    def _load_entities(self, fp):
        entity_count = 0
        entities = {}
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            if self.entity_filter and not self.entity_filter.filter(row):
                continue
            entity = EntityCreator.create(row)
            entities[entity.id] = entity
            entity_count += 1
            if self.verbose and entity_count % 10000 == 0:
                print('KB entity loading: {0: >10,}'.format(entity_count), end='\r')
        logger.info('Loaded {} entities'.format(len(entities)))
        if self.verbose:
            print('KB entity loading complete: {0: >10,}'.format(entity_count))
        return entities

    def _load_alt_names(self, fp):
        name_count = 0
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            entity_id = row[0]
            alt_name = row[1]
            if entity_id in self.entities:
                if self.name_filter and not self.name_filter.filter(alt_name):
                    continue
                self.entities[entity_id].names.add(alt_name)
                name_count += 1
                if self.verbose and name_count % 10000 == 0:
                    print('KB name loading: {0: >10,}'.format(name_count), end='\r')
        logger.info('Loaded {} alternate names'.format(name_count))
        if self.verbose:
            print('KB name loading complete: {0: >10,}'.format(name_count))

    def _write_cache(self, cache_path):
        with open(cache_path, 'wb') as cfp:
            pickle.dump(self.entities, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            self.entities = pickle.load(cfp)


class NameIndex(abc.ABC):
    """
    Find candidates based on a name string
    """
    @abc.abstractmethod
    def find(self, name, entity_type, limit=25):
        """
        Find entities that possibly match this name and type pair
        :param name: name string
        :param entity_type: EntityType string
        :param limit: maximum number of candidates to return
        :return: list of Entity objects
        """
        pass


class ExactMatchMemoryNameIndex(NameIndex):
    """
    Builds an in memory index
    """
    CACHE_NAME = 'exact-match.index.cache.pkl'

    def __init__(self, kb, cache_dir=None):
        self.kb = kb
        self.index = {}

        if cache_dir:
            cache_path = os.path.join(cache_dir, self.CACHE_NAME)
            if os.path.exists(cache_path):
                self._read_cache(cache_path)
        if not self.index:
            self.index = self._build_index()
            if cache_dir:
                self._write_cache(cache_path)

    def find(self, name, entity_type, limit=25):
        if name in self.index[entity_type]:
            return self.kb.get_entities(self.index[entity_type][name])
        else:
            return []

    def _build_index(self):
        index = {}
        for entity_type in EntityType.TYPES:
            index[entity_type] = CaseInsensitiveDict()
        for entity in self.kb:
            for name in entity.names:
                if name not in index[entity.type]:
                    index[entity.type][name] = []
                index[entity.type][name].append(entity.id)
        return index

    def _write_cache(self, cache_path):
        with open(cache_path, 'wb') as cfp:
            pickle.dump(self.index, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            self.index = pickle.load(cfp)


class NgramMemoryNameIndex(NameIndex):
    """
    An in memory ngram index
    """
    CACHE_NAME = 'ngram.index.cache.pkl'

    class Data:
        def __init__(self, num_unique_names, index):
            self.num_unique_names = num_unique_names
            self.index = index

    def __init__(self, kb, ngram_size=4, cache_dir=None):
        self.kb = kb
        self.ngram_size = ngram_size
        self.num_unique_names = 0
        self.index = {}

        if cache_dir:
            cache_path = os.path.join(cache_dir, self.CACHE_NAME)
            if os.path.exists(cache_path):
                self._read_cache(cache_path)
        if not self.index:
            self.index = self._build_index()
            if cache_dir:
                self._write_cache(cache_path)

    def find(self, name, entity_type, limit=25):
        ngrams = String.ngrams(self._format_string(name), self.ngram_size)

        # sum the idf values of ngrams for each possible name
        name_mass = collections.defaultdict(lambda: 0)
        for ngram in ngrams:
            name_ids = self.index[entity_type][ngram]
            if len(name_ids) == 0:
                continue
            idf = math.log1p(self.num_unique_names / len(name_ids))
            for name_id in name_ids:
                name_mass[name_id] += idf

        if len(name_mass) == 0:
            return []

        # select top matches based on idf mass
        threshold = max(name_mass.values()) / 2
        top = {k: v for k, v in name_mass.items() if v > threshold}
        top = sorted(top, key=top.get, reverse=True)

        if limit:
            top = top[:limit]
        return list((self.kb.get_entity(item[0]) for item in top))

    def _build_index(self):
        index = {}
        all_names = set()
        for entity_type in EntityType.TYPES:
            index[entity_type] = collections.defaultdict(list)
        for entity in self.kb:
            for i, name in enumerate(entity.names):
                all_names.add(name.lower())
                name_id = (entity.id, i)
                name = self._format_string(name)
                ngrams = String.ngrams(name, self.ngram_size)
                for ngram in ngrams:
                    index[entity.type][ngram].append(name_id)
        self.num_unique_names = len(all_names)
        return index

    @staticmethod
    def _format_string(s):
        s = String.replace_unicode_punct(s).lower()
        s = '_'.join(s.split(' '))
        return '_' + s + '_'

    def _write_cache(self, cache_path):
        data = self.Data(self.num_unique_names, self.index)
        with open(cache_path, 'wb') as cfp:
            pickle.dump(data, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            data = pickle.load(cfp)
            self.num_unique_names = data.num_unique_names
            self.index = data.index


class EntityFilter(abc.ABC):
    """
    Remove entities before populating a KB

    The LoReHLT KB has ~10 million entities with a total of ~23 million names.
    The vast majority of these entities are unrelated to the evaluation and present a scaling challenge.
    We use some heuristics to prune the list of possible entities in the KB.
    """
    @abc.abstractmethod
    def filter(self, row):
        """
        Filter the entities to only include ones that might be relevant
        :param row: list from the entities CSV file
        :return: True = include, False = exclude, None = delays decision for another filter in cascade
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


class NameFilter:
    """
    Filter alternate names when loading the kb by script.

    English is always included. Other scripts are selected from the enumeration below.
    """
    GEEZ = "ge'ez"
    ARABIC = "arabic"
    SINHALA = "sinhala"
    REGEXES = {
        GEEZ: re.compile(r'^[\u1200-\u137F]+$'),  # does not include supplement or extended
        ARABIC: re.compile(r'^[\u0600-\u06FF]+$'),  # does not include supplement or extended
        SINHALA: re.compile(r'^[\u0D80-\u0DFF]+$'),
    }

    def __init__(self, *langs):
        self.langs = langs

    def filter(self, name):
        s = String.replace_unicode_punct(name)
        s = String.replace_punct(s)
        if self.is_english(s):
            return True
        for lang in self.langs:
            if re.match(self.REGEXES[lang], s):
                return True
        return False

    @staticmethod
    def is_english(name):
        return all([ord(c) <= 127 for c in name])
