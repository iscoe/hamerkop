# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import sys
import urllib.parse

import editdistance
import numpy as np

from .core import EntityOrigin
from .utilities import CaseInsensitiveSet


class FeatureVector:
    def __init__(self):
        self.data = []

    def add(self, value):
        if isinstance(value, list):
            self.data.extend(value)
        else:
            self.data.append(value)

    def get(self):
        v = np.zeros(len(self.data))
        for index, value in enumerate(self.data):
            if isinstance(value, bool):
                v[index] = int(value)
            else:
                v[index] = value
        return v


class CorefFeature(abc.ABC):
    """
    Extract features on a pair of mention chains (clusters)
    """
    def extract(self, chain1, chain2, document):
        pass


class EntityFeature(abc.ABC):
    """
    Extract features for a mention chain and a candidate entity
    """
    def extract(self, chain, entity, document, vector):
        """
        :param chain: Mention chain
        :param entity: Candidate entity from the KB
        :param document: Document for context
        :param vector: FeatureVector to update
        """
        pass


class EntityFeatureExtractor:
    def __init__(self, *features):
        self.features = features

    def extract(self, chain, entity, document):
        v = FeatureVector()
        for feature in self.features:
            feature.extract(chain, entity, document, v)
        return v.get()


class OriginFeature(EntityFeature):
    """
    Likelihood feature based on entity origin
    """
    def __init__(self):
        self.values = {
            EntityOrigin.GEO: 1,
            EntityOrigin.AUG: 1,
            EntityOrigin.APB: 0,
            EntityOrigin.WLL: 0,
        }

    def extract(self, chain, entity, document, vector):
        vector.add(self.values[entity.origin])


class InCountryFeature(EntityFeature):
    """
    Is the entity from the country of data?
    TODO: determine country from document content
    """
    def __init__(self, *cc):
        """
        :param cc: 2 letter country codes
        """
        self.cc = cc

    def extract(self, chain, entity, document, vector):
        # TODO: not tested
        vector.add(self._get_country(entity) in self.cc)

    def _get_country(self, entity):
        country = ''
        if entity.context:
            if hasattr(entity.context, 'location'):
                country = entity.context.location
            elif hasattr(entity.context, 'country'):
                country = entity.context.country
        return country


class NumberOfNamesFeature(EntityFeature):
    """
    Entity prominence feature for GPEs and LOCs
    """
    def extract(self, chain, entity, document, vector):
        x = 1 - 1 / (1 + len(entity.names))
        vector.add(x)


class NumberOfLinksFeature(EntityFeature):
    """
    Entity prominence feature for GPEs and LOCs
    """
    def extract(self, chain, entity, document, vector):
        x = 1 - 1 / (1 + len(entity.urls))
        vector.add(x)


class WikipediaFeature(EntityFeature):
    """
    Is there an English Wikipedia link matching a mention string
    """
    def extract(self, chain, entity, document, vector):
        links = CaseInsensitiveSet({self._create_wikipedia_link(s) for s in chain.names})
        value = not links.isdisjoint(CaseInsensitiveSet(entity.urls))
        vector.add(value)

    @staticmethod
    def _create_wikipedia_link(string):
        string = string.replace(' ', '_')
        string = string.replace("’", "'")
        return "http://en.wikipedia.org/wiki/{}".format(urllib.parse.quote(string))


class ExactMatchFeature(EntityFeature):
    """
    Do the mention chain and entity share a name that is an exact match?

    Adds a boolean to the feature vector
    """
    def extract(self, chain, entity, document, vector):
        chain_names = CaseInsensitiveSet(chain.get_all_strings())
        entity_names = CaseInsensitiveSet(entity.names)
        vector.add(not chain_names.isdisjoint(entity_names))


class SharedTokensFeature(EntityFeature):
    """
    Percentage of tokens that are exact matches
    """
    def extract(self, chain, entity, document, vector):
        chain_names = CaseInsensitiveSet(chain.get_all_strings())
        entity_names = CaseInsensitiveSet(entity.names)
        percent = 0
        for x in chain_names:
            chain_name_tokens = set(x.split())
            for y in entity_names:
                entity_name_tokens = set(y.split())
                p = len(chain_name_tokens.intersection(entity_name_tokens)) / len(chain_name_tokens)
                if p > percent:
                    percent = p
        vector.add(percent)


class LastNameFeature(EntityFeature):
    """
    Does the mention chain and entity share a last name
    """
    def extract(self, chain, entity, document, vector):
        chain_names = CaseInsensitiveSet(chain.get_all_strings())
        entity_names = CaseInsensitiveSet(entity.names)
        shared_last_name = False
        for x in chain_names:
            if ' ' in x:
                for y in entity_names:
                    if ' ' in y:
                        if x.split()[-1] == y.split()[-1]:
                            shared_last_name = True
        vector.add(shared_last_name)


class LevenshteinFeature(EntityFeature):
    """
    Normalized Levenshtein edit distance
    """
    def extract(self, chain, entity, document, vector):
        chain_names = CaseInsensitiveSet(chain.get_all_strings())
        entity_names = CaseInsensitiveSet(entity.names)
        distance = float("inf")
        for x in chain_names:
            for y in entity_names:
                d = editdistance.eval(x, y) / max(len(x), len(y))
                if d < distance:
                    distance = d
        vector.add(distance)
