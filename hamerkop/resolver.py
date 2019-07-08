# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import io

from .io import LinkType


class Resolver(abc.ABC):
    """Resolve links between mention chains and kb entities"""

    @abc.abstractmethod
    def resolve(self, document):
        """
        Resolve which entity candidate is best from a list of candidates for each mention chain
        :param document: Document with mention chains and candidate sets
        """
        pass


class ResolverReport:
    """Report about Resolver Performance"""
    def __init__(self):
        # recall denominator
        self.num_mentions_with_correct_candidate = 0
        # numerator
        self.num_mentions_correct_entity = 0
        # precision denominator
        self.num_mentions_with_links = 0

    @property
    def precision(self):
        if self.num_mentions_with_links:
            return self.num_mentions_correct_entity / self.num_mentions_with_links
        else:
            return 0

    @property
    def recall(self):
        if self.num_mentions_with_correct_candidate:
            return self.num_mentions_correct_entity / self.num_mentions_with_correct_candidate
        else:
            return 0

    @property
    def f1(self):
        if self.precision + self.recall == 0:
            return 0
        return 2 * self.precision * self.recall / (self.precision + self.recall)

    def __str__(self):
        buf = io.StringIO()
        buf.write('Entity Resolution\n')
        buf.write('-----------\n')
        buf.write('P: {:.3f}  R: {:.3f}  F1: {:.3f}\n'.format(self.precision, self.recall, self.f1))
        return buf.getvalue()


class ResolverScorer:
    """Incremental Resolver Scoring"""
    def __init__(self, gt):
        """
        :param gt: Ground truth from OutputReader ({doc -> {offsets -> link}})
        """
        self.gt = gt
        self.report = ResolverReport()

    def update(self, document):
        """
        Incrementally update the scores
        :param document: Document with mention chains that have candidates and entity
        """
        if document.docid in self.gt:
            doc_gt = self.gt[document.docid]
            for chain in document.mention_chains:
                candidates = [x.id for x in chain.candidates]
                for mention in chain.mentions:
                    # precision denominator
                    if chain.entity:
                        self.report.num_mentions_with_links += 1
                    # numerator and recall denominator
                    if mention.offsets in doc_gt:
                        link = doc_gt[mention.offsets]
                        if link.link_type == LinkType.LINK:
                            if set(link.links).intersection(set(candidates)):
                                self.report.num_mentions_with_correct_candidate += 1
                                if chain.entity and chain.entity.id in link.links:
                                    self.report.num_mentions_correct_entity += 1


class FirstResolver(Resolver):
    """Select the first candidate"""
    def resolve(self, document):
        for chain in document.mention_chains:
            if chain.candidates:
                chain.entity = chain.candidates[0]
