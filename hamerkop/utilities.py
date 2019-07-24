# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import collections
import csv
import os
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

    def isdisjoint(self, other):
        return self._store.isdisjoint(other._store)

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


class DictionaryLoader:
    """Loads a dictionary from a tsv file"""
    @staticmethod
    def load(fp, lowercase_keys=True):
        d = {}
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            if lowercase_keys:
                d[row[0].strip().lower()] = row[1].strip()
            else:
                d[row[0].strip()] = row[1].strip()
        return d


class SetLoader:
    """Loads a set from a file"""
    @staticmethod
    def load(fp, lowercase=True):
        s = set()
        for line in fp.readlines():
            if lowercase:
                s.add(line.strip().lower())
            else:
                s.add(line.strip())
        return s


class TsvKeyValueCache:
    """
    File-backed dictionary cache for write once setting.
    This maintains a memory-based dictionary and periodically adds
    new elements to disk. The file on disk is added to rather than
    overwritten so this is very inefficient if changing values often.
    Call sync() before terminating the program to guarantee everything
    is written to disk.
    This is NOT thread safe.
    """
    def __init__(self, cache_dir, name, sync_period=50):
        self.filename = os.path.join(cache_dir, name + '.tsv')
        self.sync_period = sync_period
        self.data = {}
        self.new_data = {}
        self._load()

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
        self.new_data[key] = value
        if len(self.new_data) >= self.sync_period:
            self.sync()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, item):
        return item in self.data

    def _load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as fp:
                reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    self.data[row[0]] = row[1]

    def sync(self):
        with open(self.filename, 'a') as fp:
            for key in self.new_data:
                fp.write("{}\t{}\n".format(key, self.new_data[key]))
        self.new_data.clear()
