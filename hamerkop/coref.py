import abc
import collections
import io
import logging

from .core import EntityType, MentionChain
from .io import LinkType
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class Coref(abc.ABC):
    """
    Within Document Coreference

    Turns mentions into mention chains
    """
    @abc.abstractmethod
    def coref(self, document):
        """
        Process the mentions in a document to create mention chains
        :param document: Document
        """
        pass


class CorefReport:
    def __init__(self, p, r, f1):
        self.precision = p
        self.recall = r
        self.f1 = f1

    def __str__(self):
        buf = io.StringIO()
        buf.write('Indoc Coref\n')
        buf.write('-----------\n')
        buf.write('P: {:.2f}  R: {:.2f}  F1: {:.2f}\n'.format(self.precision, self.recall, self.f1))
        return buf.getvalue()


class CorefMetric:
    MUC = 'muc'
    B3 = 'b3'


class CorefScorer:
    """
    Measure the performance of a Coref system
    """
    def __init__(self, gt, metric=CorefMetric.B3):
        """
        :param gt: output of OutputReader
        """
        self.gt_clusters, self.gt_mention_map = self._prepare_gt(gt)
        if metric == CorefMetric.MUC:
            self.metric = self.muc
        elif metric == CorefMetric.B3:
            self.metric = self.b3
        else:
            raise ValueError("Unknown metric: {}".format(metric))
        self.precision_numerator = 0
        self.precision_denominator = 0
        self.recall_numerator = 0
        self.recall_denominator = 0

    def update(self, document):
        """
        Update performance metrics with the mention chains from this document
        :param document: Document with mention chains
        """
        # prepare clusters and mention map
        predicted_clusters = []
        for chain in document.mention_chains:
            predicted_clusters.append([self._create_mention_id(m.offsets) for m in chain.mentions])
        predicted_mention_map = self._create_mention_map(predicted_clusters)

        self._update_metrics(document.docid, predicted_clusters, predicted_mention_map)

    def _update_metrics(self, doc_id, predicted_clusters, predicted_mention_map):
        p_num, p_den = self.metric(predicted_clusters, self.gt_mention_map[doc_id])
        r_num, r_den = self.metric(self.gt_clusters[doc_id], predicted_mention_map)
        self.precision_numerator += p_num
        self.precision_denominator += p_den
        self.recall_numerator += r_num
        self.recall_denominator += r_den

    @property
    def precision(self):
        if self.precision_numerator == 0:
            return 0
        else:
            return self.precision_numerator / self.precision_denominator

    @property
    def recall(self):
        if self.recall_numerator == 0:
            return 0
        else:
            return self.recall_numerator / self.recall_denominator

    @property
    def f1(self):
        if self.precision + self.recall == 0:
            return 0
        return 2 * self.precision * self.recall / (self.precision + self.recall)

    @property
    def report(self):
        return CorefReport(self.precision, self.recall, self.f1)

    @staticmethod
    def muc(clusters, mention_map):
        tp = p = 0
        for c in clusters:
            p += len(c) - 1
            tp += len(c)
            linked = set()
            for m in c:
                if m in mention_map:
                    linked.add(mention_map[m])
                else:
                    tp -= 1
            tp -= len(linked)
            print(tp)
        return tp, p

    @staticmethod
    def b3(clusters, mention_map):
        num = dem = 0
        for c in clusters:
            if len(c) == 1:
                continue
            gt_counts = collections.Counter()
            correct = 0
            for m in c:
                if m in mention_map:
                    gt_counts[mention_map[m]] += 1
            for c2, count in gt_counts.items():
                if len(c2) != 1:
                    correct += count * count
            num += correct / len(c)
            dem += len(c)
        return num, dem

    @classmethod
    def _prepare_gt(cls, gt):
        """
        Takes in doc_id -> offsets -> list of links (see OutputReader)
        Creates two dictionaries:
           doc_id -> list of mention ID clusters
           doc_id -> mention ID -> cluster ID
        """
        # create lists of mentions for each cluster in a document
        gt_clusters = {}
        for doc in gt:
            gt_clusters[doc] = []
            clusters = collections.defaultdict(list)
            for offsets in gt[doc]:
                cluster_id = cls._create_cluster_id(gt[doc][offsets])
                clusters[cluster_id].append(cls._create_mention_id(offsets))
            gt_clusters[doc] = list(clusters.values())

        # creates mapping from mention ID to cluster ID
        gt_mention_map = {}
        for doc in gt_clusters:
            gt_mention_map[doc] = cls._create_mention_map(gt_clusters[doc])

        return gt_clusters, gt_mention_map

    @staticmethod
    def _create_mention_id(offsets):
        return 'm-' + str(offsets[0]) + '-' + str(offsets[1])

    @staticmethod
    def _create_cluster_id(link):
        if link.link_type == LinkType.NIL:
            return link.cluster
        else:
            return '|'.join(link.links)

    @staticmethod
    def _create_mention_map(clusters):
        cluster_counter = 0
        mention_map = {}
        for cluster in clusters:
            cluster_counter += 1
            cluster_id = 'C' + str(cluster_counter)
            for mention_id in cluster:
                mention_map[mention_id] = cluster_id
        return mention_map


class CorefUpdate(abc.ABC):
    """
    Update the current mention chains (split or merge)
    """
    @abc.abstractmethod
    def update(self, document):
        """
        Process the current mention chains to merge or split some
        :param document: Document
        """
        pass

    def merge(self, chains, *to_merge):
        logger.debug('{} merging {}'.format(self.__class__.__name__, to_merge))
        new_chain = MentionChain(sum([chain.mentions for chain in to_merge], []))
        chains = [x for x in chains if x not in to_merge]
        chains.append(new_chain)
        return chains


class TwoStageCoref(Coref):
    """
    Create mention chains with a Coref component and then update with one or more CorefUpdate components
    """
    def __init__(self, coref, updaters):
        self._coref = coref
        self._updaters = updaters

    def coref(self, document):
        self._coref.coref(document)
        for updater in self._updaters:
            updater.update(document)


class UnchainedCoref(Coref):
    """
    Each mention gets its own chain
    """
    def coref(self, document):
        document.mention_chains = [MentionChain([mention]) for mention in document.mentions]


class ExactMatchCoref(Coref):
    """
    Mentions strings that are exact matches are chained (case not considered)
    """
    def coref(self, document):
        chain_data = {}
        for entity_type in EntityType.TYPES:
            chain_data[entity_type] = CaseInsensitiveDict()
        for mention in document.mentions:
            if mention.string not in chain_data[mention.type]:
                chain_data[mention.type][mention.string] = []
            chain_data[mention.type][mention.string].append(mention)
        document.mention_chains = []
        for entity_type in chain_data:
            chains = [MentionChain(chain) for chain in chain_data[entity_type].values()]
            document.mention_chains.extend(chains)


class CorefAcronymUpdate(CorefUpdate):
    """
    Finds best match for names that look like acronyms

    This only works for scripts that support case.
    This does not handle words that are dropped like 'of'.
    """
    def __init__(self, min_length):
        """
        :param min_length: Minimum length in characters
        """
        self.min_length = min_length

    def update(self, document):
        acronym_chains = [chain for chain in document.mention_chains if self.is_acronym(chain.name)]
        if acronym_chains:
            other_chains = [(chain, self.create_acronym(chain.name)) for chain in document.mention_chains
                            if chain not in acronym_chains]
            for acronym_chain in acronym_chains:
                matches = []
                for chain, acronym in other_chains:
                    if acronym_chain.type != chain.type:
                        continue
                    if acronym_chain.name == acronym:
                        matches.append(chain)
                if matches:
                    matches = self.rank(acronym_chain, matches)
                    document.mention_chains = self.merge(document.mention_chains, acronym_chain, matches[0])

    @staticmethod
    def rank(acronym_chain, matches):
        # TODO for now default to first instance
        return matches

    def is_acronym(self, string):
        if len(string) < self.min_length:
            return False
        return string.upper() == string

    @staticmethod
    def create_acronym(string):
        return ''.join(word[0].upper() for word in string.split())
