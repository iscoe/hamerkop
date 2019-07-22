# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import copy
import io
import logging

from .core import EntityType, LinkType, MentionChain
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
        buf.write('P: {:.3f}  R: {:.3f}  F1: {:.3f}\n'.format(self.precision, self.recall, self.f1))
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

        self._update_metrics(document.doc_id, predicted_clusters, predicted_mention_map)

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
            return link.cluster_id
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


class CascadeCoref(Coref):
    """
    Implementation of Stanford Sieve.

    Every mentions starts as its own cluster (mention chain).
    Each stage gets to merge clusters (or possibly split).
    Typically, the sieve starts with the highest precision stages.
    """
    def __init__(self, stages):
        self.stages = stages

    def coref(self, document):
        document.mention_chains = [MentionChain([mention]) for mention in document.mentions]
        for stage in self.stages:
            stage.update(document)


class CorefStage(abc.ABC):
    """
    Update the current mention chains (split or merge)
    """
    @abc.abstractmethod
    def update(self, document):
        """
        Process the current mention chains
        :param document: Document
        """
        pass

    def merge(self, document, to_merge):
        logger.debug('{} merging {}'.format(self.__class__.__name__, to_merge))
        # make sure no duplicates
        to_merge = list(set(to_merge))
        # sum starts with 0 by default so we start with []
        new_chain = MentionChain(sum([chain.mentions for chain in to_merge], []))
        chains = [x for x in document.mention_chains if x not in to_merge]
        chains.append(new_chain)
        document.mention_chains = chains


class LanguageSpecificStage(CorefStage):
    """
    Coref stage that only runs if doc is a particular language(s)
    """
    def __init__(self, stage, *langs):
        self.stage = stage
        self.langs = langs

    def update(self, document):
        if document.lang in self.langs:
            self.stage.update(document)


class TypeSpecificStage(CorefStage):
    """
    Coref stage that only runs if entity is a particular type(s)
    """
    def __init__(self, stage, *types):
        self.stage = stage
        self.types = types

    def update(self, document):
        other_chains = [x for x in document.mention_chains if x.type not in self.types]
        chains = [x for x in document.mention_chains if x.type in self.types]
        document.mention_chains = chains
        self.stage.update(document)
        document.mention_chains += other_chains


class ExactMatchStage(CorefStage):
    """
    Mentions strings that are exact matches are chained (case insensitive)
    """
    def update(self, document):
        # find mention chains that share a name string
        chain_data = collections.defaultdict(CaseInsensitiveDict)
        for chain in document.mention_chains:
            for mention in chain.mentions:
                if mention.string not in chain_data[mention.type]:
                    chain_data[mention.type][mention.string] = []
                chain_data[mention.type][mention.string].append(chain)
        # merge them
        for entity_type in chain_data:
            for name, chains in chain_data[entity_type].items():
                if len(chains) > 1:
                    self.merge(document, chains)


class AcronymStage(CorefStage):
    """
    Finds names that match name strings identified as acronyms

    This only works for scripts that support case.
    This does not handle words that are dropped like 'of'.
    This works better after exact name match.
    This assumes that the acronym mentions have not been matched
      with any other mentions (besides the same acronym string).
    """
    def __init__(self, min_length):
        """
        :param min_length: Minimum length in characters
        """
        self.min_length = min_length

    def update(self, document):
        chains = copy.copy(document.mention_chains)
        possible_acronyms = {}
        for chain in chains:
            acronym = self._get_acronym(chain)
            if acronym:
                possible_acronyms[chain] = acronym
        for chain, acronym in possible_acronyms.items():
            merged_chain = None
            for other_chain in chains:
                if chain.type == other_chain.type and self._is_match(acronym, other_chain):
                    self.merge(document, [chain, other_chain])
                    merged_chain = other_chain
                    # only matching to first potential match.
                    # likely better to use token offset distance.
                    # also this assumes exact name matches have been chained already.
                    break
            # we cannot let a chain merge separately to 2 separate chains as it duplicates the mentions.
            # it would probably be better to update a list of merges and process them all at the end.
            if merged_chain is not None:
                chains.remove(merged_chain)

    def _get_acronym(self, chain):
        for mention in chain.mentions:
            if len(mention.string) < self.min_length:
                continue
            if mention.string.upper() == mention.string:
                return mention.string

    @staticmethod
    def _is_match(acronym, chain):
        for mention in chain.mentions:
            if acronym == ''.join(word[0].upper() for word in mention.string.split()):
                return True
        return False


class SingleTokenMatchStage(CorefStage):
    """
    Combine mentions where a single token name matches a longer name string.

    Specify the which token to match on to select between first name or last name for people.
    Use this in combination with the TypeSpecificStage to restrict to people or other entity types.
    Warning: this is very aggressive and will combine everyone that share the name token.
    TODO: add check if more than one entity shares the token and reject if so.
    """
    def __init__(self, index):
        """
        :param index: integer index into the tokenized name. 0 is first token and -1 is last token
        """
        self.index = index

    def update(self, document):
        single_token_name_chains = {}
        for chain in document.mention_chains:
            name = self._get_single_token_name(chain)
            if name:
                single_token_name_chains[chain] = name

        for single_chain, single_name in single_token_name_chains.items():
            matches = [chain for chain in document.mention_chains if self._is_match(single_name, single_chain, chain)]
            if matches:
                matches.append(single_chain)
                self.merge(document, matches)

    def _get_single_token_name(self, chain):
        for mention in chain.mentions:
            # only using the first single token in the chain
            if ' ' not in mention.string:
                return mention.string
        return None

    def _is_match(self, single_name, single_chain, chain):
        if single_chain.type != chain.type:
            return False

        for mention in chain.mentions:
            if ' ' in mention.string:
                possible_partial_name = mention.string.split()[self.index]
                if single_name.lower() == possible_partial_name.lower():
                    return True
        return False
