import collections
import csv
from .core import Mention, Document
from .lang import NgramLangDetector
from .utilities import InProcessIncremental


class InputReader:
    def __init__(self, fp, id_assigner=None, lang_detector=None):
        self.reader = read_conll(fp)
        if id_assigner is None:
            id_assigner = InProcessIncremental()
        if lang_detector is None:
            lang_detector = NgramLangDetector()
        self.preparer = DocumentPreparer(id_assigner, lang_detector)

    def __iter__(self):
        return self

    def __next__(self):
        return self.preparer.process(next(self.reader))


Row = collections.namedtuple('Row', 'token tag docid offsets')


class CoNLLReaderException(Exception):
    """An error occurred when reading and parsing a CoNLL file."""


def read_conll(fp):
    """
    Generator that returns a list of Row tuples for each document
    :param fp: handle to CoNLL tsv file with columns: token tag token docid start stop sentence
    :return: list of Row tuples
    """
    reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
    first_row = next(reader)
    if not first_row:
        raise CoNLLReaderException("csv reader cannot read first line of {}".format(fp.name))
    if first_row[0].lower() in ['token', 'tok']:
        raise CoNLLReaderException("Reader does not handle file with header: {}".format(fp.name))
    fp.seek(0)

    token_index = 0
    tag_index = 1
    docid_index = 3
    offsets_indexes = (4, 5)

    rows = []
    current_docid = None
    for row in reader:
        if len(row) < 6:
            # sentence breaks are ignored
            continue

        if not row[tag_index]:
            raise RuntimeError("Bad conll format data: {}".format(row))

        if current_docid is None:
            current_docid = row[docid_index]

        if row[docid_index] != current_docid:
            yield rows
            rows = []
            current_docid = row[docid_index]

        start = int(row[offsets_indexes[0]])
        stop = int(row[offsets_indexes[1]])
        rows.append(Row(row[token_index], row[tag_index], row[docid_index], (start, stop)))
    yield rows


class DocumentPreparer(object):
    """
    Prepare a document from a list of rows extracted from tagged conll file
    This does not check for conditions like B-PER I-ORG.
    This passes all tag types so B-DOG will end up as a mention.
    """

    def __init__(self, id_assigner, lang_detector):
        self.id_assigner = id_assigner
        self.lang_detector = lang_detector

    def process(self, rows):
        """
        Turn a list of rows into entity mentions
        :param rows: list of Row namedtuples
        :return: Document or None if no mentions
        """
        tokens = []
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
            token_index += 1

        if in_mention:
            mentions.append(self._extract(mention_rows, token_start))

        if mentions:
            filename = mentions[0].docid
            lang = self.lang_detector.detect(filename, tokens)
            return Document(mentions, tokens, lang)

    def _extract(self, rows, token_start):
        first_row = rows.pop(0)
        name = first_row.token
        ch_start = first_row.offsets[0]
        ch_stop = first_row.offsets[1]
        token_stop = token_start + 1
        docid = first_row.docid
        type = first_row.tag[2:]
        for row in rows:
            name = ' '.join((name, row.token))
            ch_stop = row.offsets[1]
            token_stop += 1
        token_offsets = (token_start, token_stop)
        mention = Mention(name, docid, (ch_start, ch_stop), token_offsets, type)
        self.id_assigner.assign(mention)
        return mention


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
                doc_info = "{}:{}-{}".format(mention.docid, *mention.offsets)
                line = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    self.system, mention.id, mention.original_string, doc_info,
                    entity, mention.type, 'NAM', self.prob)
                self.fp.write(line)


# link from a ground truth file
Link = collections.namedtuple('Link', 'entity_type link_type links cluster')


class LinkType:
    NIL = False
    LINK = True


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
            doc_id = row[EvalTabFormat.DOC_AND_OFFSETS].split(':')[0]
            offset_strings = row[EvalTabFormat.DOC_AND_OFFSETS].split(':')[1].split('-')
            offsets = tuple(map(int, offset_strings))
            link_type = 'NIL' not in row[EvalTabFormat.KB_ID]
            links = []
            cluster = None
            if link_type == LinkType.LINK:
                links = row[EvalTabFormat.KB_ID].split('|')
            else:
                cluster = row[EvalTabFormat.KB_ID]
            data[doc_id][offsets] = Link(row[EvalTabFormat.ENTITY_TYPE], link_type, links, cluster)
        return data
