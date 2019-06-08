import collections
import csv


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
Link = collections.namedtuple('Link', 'entity_type link_type links')


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
            if link_type == LinkType.LINK:
                links = row[EvalTabFormat.KB_ID].split('|')
            data[doc_id][offsets] = Link(row[EvalTabFormat.ENTITY_TYPE], link_type, links)
        return data
