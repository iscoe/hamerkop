# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import io
import urllib.parse

from .core import EntityType, LinkType
from .utilities import CaseInsensitiveSet


class ResolverReport:
    """
    Report about Resolver Performance.

    This contains P, R, and F1 statistics for mentions broken down by entity type.
    """
    def __init__(self):
        # numerator
        self.num_mentions_correct_entity = collections.defaultdict(int)
        # recall denominator
        self.num_mentions_with_correct_candidate = collections.defaultdict(int)
        # precision denominator
        self.num_mentions_with_links = collections.defaultdict(int)
        self.wrong_entity_links = collections.defaultdict(collections.Counter)
        self.type_1_errors = collections.defaultdict(collections.Counter)

    def update(self, name, entity_type, correct=None):
        """
        :param name: Mention name
        :param entity_type: Entity type
        :param correct: Was the correct entity chosen if in candidate set (None means false alarm)
        """
        if correct is not None:
            self.num_mentions_with_correct_candidate[entity_type] += 1
            if correct:
                self.num_mentions_correct_entity[entity_type] += 1
            else:
                self.wrong_entity_links[entity_type].update({name: 1})
        else:
            self.type_1_errors[entity_type].update({name: 1})

    @property
    def precision(self):
        num_mentions_with_links = sum(self.num_mentions_with_links.values())
        if num_mentions_with_links:
            return sum(self.num_mentions_correct_entity.values()) / num_mentions_with_links
        else:
            return 0

    @property
    def recall(self):
        num_mentions_with_correct_candidate = sum(self.num_mentions_with_correct_candidate.values())
        if num_mentions_with_correct_candidate:
            return sum(self.num_mentions_correct_entity.values()) / num_mentions_with_correct_candidate
        else:
            return 0

    @property
    def f1(self):
        if self.precision + self.recall == 0:
            return 0
        return 2 * self.precision * self.recall / (self.precision + self.recall)

    def get_precision_by_type(self, entity_type):
        if self.num_mentions_with_links[entity_type]:
            return self.num_mentions_correct_entity[entity_type] / self.num_mentions_with_links[entity_type]
        else:
            return 0

    def get_recall_by_type(self, entity_type):
        if self.num_mentions_with_correct_candidate[entity_type]:
            return self.num_mentions_correct_entity[entity_type] / self.num_mentions_with_correct_candidate[entity_type]
        else:
            return 0

    def get_f1_by_type(self, entity_type):
        p = self.get_precision_by_type(entity_type)
        r = self.get_recall_by_type(entity_type)
        if p + r == 0:
            return 0
        return 2 * p * r / (p + r)

    def get_stats_by_type(self, entity_type):
        return self.get_precision_by_type(entity_type), \
               self.get_recall_by_type(entity_type), \
               self.get_f1_by_type(entity_type)

    def __str__(self):
        buf = io.StringIO()
        buf.write('Entity Resolution\n')
        buf.write('-----------\n')
        buf.write('P: {:.3f}  R: {:.3f}  F1: {:.3f}\n'.format(self.precision, self.recall, self.f1))
        for entity_type in EntityType.TYPES:
            buf.write('  {} P: {:.3f}  R: {:.3f}  F1: {:.3f}  {}\n'.format(
                entity_type, *self.get_stats_by_type(entity_type), self.num_mentions_with_links[entity_type]))
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
                        self.report.num_mentions_with_links[chain.type] += 1
                    # numerator and recall denominator
                    if mention.offsets in doc_gt:
                        link = doc_gt[mention.offsets]
                        if link.link_type == LinkType.LINK:
                            if set(link.links).intersection(set(candidates)):
                                correct = chain.entity and chain.entity.id in link.links
                                self.report.update(mention.string, link.entity_type, correct=correct)
                        elif chain.entity:
                            # mention has a selected candidate but is NIL in ground truth
                            self.report.update(mention.string, mention.type)


class Resolver(abc.ABC):
    """
    Resolve links between mention chains and kb entities.

    A resolver can select the entity that is the best link from the list of candidates.
    It can also eliminate candidates from consideration from downstream resolvers if using a cascade.
    """

    @abc.abstractmethod
    def resolve(self, document):
        """
        Resolve which entity candidate is best from a list of candidates for each mention chain
        :param document: Document with mention chains and candidate sets
        """
        pass


class CascadeResolver(Resolver):
    """
    Cascade over several resolvers.
    Each resolver can filter out candidates reducing the number for the next resolver.
    """
    def __init__(self, resolvers):
        """
        :param resolvers: list of Resolver objects
        """
        self.resolvers = resolvers

    def resolve(self, document):
        # after each round removes the mention chains that have been resolved
        resolved = []
        for resolver in self.resolvers:
            resolver.resolve(document)
            new_resolved = [chain for chain in document.mention_chains if chain.entity is not None]
            resolved.extend(new_resolved)
            document.mention_chains = [chain for chain in document.mention_chains if chain.entity is None]
            if not document.mention_chains:
                break
        document.mention_chains.extend(resolved)


class FirstResolver(Resolver):
    """Select the first candidate"""
    def resolve(self, document):
        for chain in document.mention_chains:
            if chain.candidates:
                chain.entity = chain.candidates[0]


class ExactNameResolver(Resolver):
    """
    Select the match by exact name match.

    If only one exact match, selects that candidate.
    If multiple exact matches, reduces candidates to that list.
    If no exact matches, takes no action.
    """
    def resolve(self, document):
        for chain in document.mention_chains:
            matches = []
            names = CaseInsensitiveSet(chain.names)
            for candidate in chain.candidates:
                if names & CaseInsensitiveSet(candidate.names):
                    matches.append(candidate)
            if matches:
                if len(matches) == 1:
                    chain.entity = matches[0]
                else:
                    chain.candidates = matches


class WikipediaResolver(Resolver):
    """
    Use the Entity urls to resolve the mention.

    If only one match, selects that candidate.
    If multiple matches, reduces candidates to that list.
    If no matches, returns all candidates.

    This does not handle places that include an administrative district in their wikipedia url.
    For example, https://en.wikipedia.org/wiki/Columbia,_Maryland
    """
    def resolve(self, document):
        for chain in document.mention_chains:
            matches = []
            links = CaseInsensitiveSet({self._create_wikipedia_link(s) for s in chain.names})
            for candidate in chain.candidates:
                if links & CaseInsensitiveSet(candidate.urls):
                    matches.append(candidate)
            if matches:
                if len(matches) == 1:
                    chain.entity = matches[0]
                else:
                    chain.candidates = matches

    @staticmethod
    def _create_wikipedia_link(string):
        string = string.replace(' ', '_')
        string = string.replace("’", "'")
        return "http://en.wikipedia.org/wiki/{}".format(urllib.parse.quote(string))
