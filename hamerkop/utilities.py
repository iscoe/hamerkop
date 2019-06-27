# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import timeit


class CaseInsensitiveSet(collections.MutableSet):
    """
    Case Insensitive Set
    This does not implement any of the set operations like union or intersection.
    It does support adding, removing, and testing membership.
    """
    def __init__(self, data=None):
        self._store = set()
        if data is not None:
            self.update(data)

    def add(self, item):
        self._store.add(item.lower())

    def update(self, items):
        for item in items:
            self.add(item)

    def discard(self, item):
        self._store.discard(item.lower())

    def __contains__(self, item):
        return item.lower() in self._store

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return self._store.__iter__()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._store)


class CaseInsensitiveDict(collections.MutableMapping):
    """
    Wraps a dictionary forcing all key operations to be lower case
    """
    def __init__(self, data=None):
        self._store = dict()
        if data is not None:
            self.update(data)

    def __setitem__(self, key, value):
        self._store[key.lower()] = value

    def __getitem__(self, key):
        return self._store[key.lower()]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __contains__(self, key):
        return self._store.__contains__(key.lower())

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return self._store.__iter__()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._store)


class Identifier(abc.ABC):
    """Create unique identifiers"""
    @abc.abstractmethod
    def assign(self, mention):
        """
        Assign an identifier to a mention
        :param mention: Mention
        :return reference to the mention passed to method
        """
        pass


class InProcessIncremental(Identifier):
    """Non-parallel processing safe identifier assigner"""
    def __init__(self):
        self.count = 1

    def assign(self, mention):
        mention.id = "M{}".format(self.count)
        self.count += 1
        return mention


class Timer:
    def __init__(self, name=None):
        self.name = name
        self.time = 0

    def __enter__(self):
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.time += timeit.default_timer() - self.start


class NotATimer:
    def __init__(self, name=None):
        self.name = name
        self.time = 0

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
