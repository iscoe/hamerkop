# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
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


class CorefFeatureExtractor(abc.ABC):
    """
    Extract features on a pair of mention chains (clusters)
    """
    def extract(self, chain1, chain2, document):
        pass


class EntityFeatureExtractor(abc.ABC):
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


class ExactMatchExtractor(EntityFeatureExtractor):
    """
    Do the mention chain and entity share a name that is an exact match?

    Adds a boolean to the feature vector
    """
    def extract(self, chain, entity, document, vector):
        chain_names = CaseInsensitiveSet()
        for mention in chain.mentions:
            chain_names.add(mention.string)
            if mention.translit_string:
                chain_names.add(mention.translit_string)
            if mention.translate_string:
                chain_names.add(mention.translate_string)

        entity_names = CaseInsensitiveSet(entity.names)
        vector.add(not chain_names.isdisjoint(entity_names))
