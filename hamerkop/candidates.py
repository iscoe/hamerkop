# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import io
import logging

from .io import LinkType

logger = logging.getLogger(__name__)


class CandidateGenerator(abc.ABC):
    """
    A candidate generator finds reasonable candidates for mention chains.
    """

    def process(self, document):
        """
        Process a document of mention chains
        :param document: Document with mention chains
        """
        self.document = document
        for chain in document.mention_chains:
            chain.candidates = self.find(chain)

    @abc.abstractmethod
    def find(self, mention_chain):
        """
        Find candidates for a mention chain
        :param mention_chain: MentionChain object with list of mentions
        :return: List of candidates
        """
        pass


class CandidatesReport:
    def __init__(self):
        self.num_mentions_with_links = 0
        self.num_including_correct_entity = 0

    @property
    def recall(self):
        if self.num_mentions_with_links:
            return self.num_including_correct_entity / self.num_mentions_with_links
        else:
            return 0

    def __str__(self):
        buf = io.StringIO()
        buf.write('Candidate Generation\n')
        buf.write('--------------------\n')
        buf.write('R: {:.3f}\n'.format(self.recall))
        return buf.getvalue()


class CandidatesScorer:
    def __init__(self, gt):
        """
        :param gt: Ground truth from OutputReader ({doc -> {offsets -> link}})
        """
        self.gt = gt
        self.report = CandidatesReport()

    def update(self, document):
        if document.docid in self.gt:
            doc_gt = self.gt[document.docid]
            for chain in document.mention_chains:
                candidates = [x.id for x in chain.candidates]
                for mention in chain.mentions:
                    if mention.offsets in doc_gt:
                        link = doc_gt[mention.offsets]
                        if link.link_type == LinkType.LINK:
                            self.report.num_mentions_with_links += 1
                            if set(link.links).intersection(set(candidates)):
                                self.report.num_including_correct_entity += 1


class IndexBasedGenerator(CandidateGenerator):
    """
    Use a NameIndex to find candidates for entity linking.

    Only uses the "best" name from the mention chain.
    """
    def __init__(self, index, maximum=25):
        self.index = index
        self.max = maximum

    def find(self, mention_chain):
        name = mention_chain.name
        candidates = self.index.find(name, mention_chain.type, self.max)
        logger.debug("{}({}): {} candidates from {}".format(
            name, mention_chain.type, len(candidates), type(self.index).__name__))
        return candidates


class CombiningGenerator(CandidateGenerator):
    """
    Combines all candidates from its generators
    """
    def __init__(self, generators):
        """
        :param generators: list of CandidateGenerators
        """
        self.generators = generators

    def find(self, mention_chain):
        candidate_dict = {}
        for generator in self.generators:
            for entity in generator.find(mention_chain):
                candidate_dict[entity.id] = entity
        logger.debug("{}({}): {} total candidates".format(mention_chain.name, mention_chain.type, len(candidate_dict)))
        return list(candidate_dict.values())


class CascadeGenerator(CandidateGenerator):
    """
    Call each generator in the cascade until all slots are filled
    """
    def __init__(self, generators, num_candidates=25):
        """
        :param generators: list of CandidateGenerators
        :param num_candidates: stop the cascade after this number is surpassed
        """
        self.generators = generators
        self.num_candidates = num_candidates

    def find(self, mention_chain):
        candidate_dict = {}
        for generator in self.generators:
            for entity in generator.find(mention_chain):
                candidate_dict[entity.id] = entity
            if len(candidate_dict) >= self.num_candidates:
                break
        logger.debug("{}({}): {} total candidates".format(mention_chain.name, mention_chain.type, len(candidate_dict)))
        return list(candidate_dict.values())


class CachingGenerator(CandidateGenerator):
    """
    Caches candidates based on the mention chain (name and type).
    This is a memory cache.
    """
    def __init__(self, generator):
        """
        :param generator: CandidateGenerator to cache the results from
        """
        self.generator = generator
        self.cache = {}

    def find(self, mention_chain):
        key = self._gen_key(mention_chain)
        if key in self.cache:
            return self.cache[key]
        candidates = self.generator.find(mention_chain)
        self.cache[key] = candidates
        return candidates

    def _gen_key(self, mention_chain):
        return mention_chain.name.lower() + ':' + mention_chain.type
