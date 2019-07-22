# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import logging
import math
import os
import pickle

from .core import EntityType, LinkType
from .string import String
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class KBException(Exception):
    """An error occurred when interacting with the KB."""


class KB(abc.ABC):
    """
    Knowledge base interface
    Provides methods for retrieving entities but not searching for them.
    See NameIndex for search methods.
    """

    @abc.abstractmethod
    def size(self):
        """
        Get the number of entities in the KB
        :return: int
        """
        pass

    @abc.abstractmethod
    def get_entity(self, entity_id):
        """
        Get an entity
        :param entity_id: string
        :return: Entity
        """
        pass

    @abc.abstractmethod
    def get_entities(self, entity_ids):
        """
        Get a list of entities
        :param entity_ids: list of entity ids
        :return: list
        """
        pass




class KBLoadingScorer:
    def __init__(self, kb, gt):
        self.kb = kb
        self.ids = self._prepare(gt)
        self.recall = 0
        self.missed = set()

    def score(self):
        in_kb_count = 0
        for entity_id in self.ids:
            if self.kb.get_entity(entity_id):
                in_kb_count += 1
            else:
                self.missed.add(entity_id)
        self.recall = in_kb_count / len(self.ids)

    def _prepare(self, gt):
        ids = set()
        for doc in gt:
            for link in gt[doc].values():
                if link.link_type == LinkType.LINK:
                    ids.update(link.links)
        return ids


class MemoryKB(KB):
    """
    KB backed by a python dictionary for smaller kbs.

    The dictionary is entity ID -> Entity object
    """
    CACHE_FILE = 'memorykb.cache.pkl'

    def __init__(self, entity_loader, cache_dir=None, verbose=False):
        """
        :param entity_loader: Loads entities from disk or db into memory
        :param cache_dir: Optional path to directory to cache the KB
        :param verbose: Whether to use stdout for updates
        """
        self.entities = {}
        if cache_dir:
            cache_path = os.path.join(cache_dir, self.CACHE_FILE)
            if os.path.exists(cache_path):
                if verbose:
                    print("Loading entities from the cache")
                self.entities = self._read_cache(cache_path)
        if not self.entities:
            self.entities = entity_loader.load()
            if cache_dir:
                self._write_cache(cache_path)

    def size(self):
        return len(self.entities)

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def get_entities(self, entity_ids):
        return [self.entities[x] for x in entity_ids if x in self.entities]

    def __iter__(self):
        for entity in self.entities.values():
            yield entity

    def _write_cache(self, cache_path):
        with open(cache_path, 'wb') as cfp:
            pickle.dump(self.entities, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            return pickle.load(cfp)


class NameIndex(abc.ABC):
    """
    Find candidates based on a name string
    """
    @abc.abstractmethod
    def find(self, name, entity_type, limit=25):
        """
        Find entities that possibly match this name and type pair
        :param name: name string
        :param entity_type: EntityType string
        :param limit: maximum number of candidates to return
        :return: list of Entity objects
        """
        pass


class ExactMatchMemoryNameIndex(NameIndex):
    """
    Builds an in memory index
    """
    CACHE_FILE = 'exact-match.index.cache.pkl'

    def __init__(self, kb, cache_dir=None):
        self.kb = kb
        self.index = {}

        if cache_dir:
            cache_path = os.path.join(cache_dir, self.CACHE_FILE)
            if os.path.exists(cache_path):
                self.index = self._read_cache(cache_path)
        if not self.index:
            self.index = self._build_index()
            if cache_dir:
                self._write_cache(cache_path)

    def find(self, name, entity_type, limit=25):
        if name in self.index[entity_type]:
            return self.kb.get_entities(self.index[entity_type][name])
        else:
            return []

    def _build_index(self):
        index = {}
        for entity_type in EntityType.TYPES:
            index[entity_type] = CaseInsensitiveDict()
        for entity in self.kb:
            for name in entity.names:
                if name not in index[entity.type]:
                    index[entity.type][name] = []
                index[entity.type][name].append(entity.id)
        return index

    def _write_cache(self, cache_path):
        with open(cache_path, 'wb') as cfp:
            pickle.dump(self.index, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            return pickle.load(cfp)


class NgramMemoryNameIndex(NameIndex):
    """
    An in memory ngram index
    """
    CACHE_FILE = 'ngram.index.cache.pkl'

    class Data:
        def __init__(self, num_unique_names, index):
            self.num_unique_names = num_unique_names
            self.index = index

    def __init__(self, kb, ngram_size=4, cache_dir=None):
        self.kb = kb
        self.ngram_size = ngram_size
        self.num_unique_names = 0
        self.index = {}

        if cache_dir:
            cache_path = os.path.join(cache_dir, self.CACHE_FILE)
            if os.path.exists(cache_path):
                self.index = self._read_cache(cache_path)
        if not self.index:
            self.index = self._build_index()
            if cache_dir:
                self._write_cache(cache_path)

    def find(self, name, entity_type, limit=25):
        ngrams = String.ngrams(self._format_string(name), self.ngram_size)

        # sum the idf values of ngrams for each possible name
        name_mass = collections.defaultdict(lambda: 0)
        for ngram in ngrams:
            name_ids = self.index[entity_type][ngram]
            if len(name_ids) == 0:
                continue
            idf = math.log1p(self.num_unique_names / len(name_ids))
            for name_id in name_ids:
                name_mass[name_id] += idf

        if len(name_mass) == 0:
            return []

        # select top matches based on idf mass
        threshold = max(name_mass.values()) / 2
        top = {k: v for k, v in name_mass.items() if v > threshold}
        top = sorted(top, key=top.get, reverse=True)

        if limit:
            top = top[:limit]
        return list((self.kb.get_entity(item[0]) for item in top))

    def _build_index(self):
        index = {}
        all_names = set()
        for entity_type in EntityType.TYPES:
            index[entity_type] = collections.defaultdict(list)
        for entity in self.kb:
            for i, name in enumerate(entity.names):
                all_names.add(name.lower())
                name_id = (entity.id, i)
                name = self._format_string(name)
                ngrams = String.ngrams(name, self.ngram_size)
                for ngram in ngrams:
                    index[entity.type][ngram].append(name_id)
        self.num_unique_names = len(all_names)
        return index

    @staticmethod
    def _format_string(s):
        s = String.replace_unicode_punct(s).lower()
        s = '_'.join(s.split(' '))
        return '_' + s + '_'

    def _write_cache(self, cache_path):
        data = self.Data(self.num_unique_names, self.index)
        with open(cache_path, 'wb') as cfp:
            pickle.dump(data, cfp)

    def _read_cache(self, cache_path):
        with open(cache_path, 'rb') as cfp:
            data = pickle.load(cfp)
            self.num_unique_names = data.num_unique_names
            return data.index


class TypeIgnoringIndex(NameIndex):
    """
    Ignores some type distinctions.

    Will return up to n * limit entities where n is the number of types to conflate.
    """
    def __init__(self, index, *types):
        """
        :param index: NameIndex to wrap
        :param types: sets of entity types that should be queried at the same time
        """
        self.index = index
        self.type_map = {}
        for type_set in types:
            for t in type_set:
                if t not in self.type_map:
                    self.type_map[t] = set()
                self.type_map[t].update(type_set)

    def find(self, name, entity_type, limit=25):
        if entity_type in self.type_map:
            entities = {}
            for et in self.type_map:
                for entity in self.index.find(name, et, limit):
                    entities[entity.id] = entity
            return list(entities.values())
        else:
            return self.index.find(name, entity_type, limit)
