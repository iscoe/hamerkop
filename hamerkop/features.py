# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import editdistance
import numpy as np

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
