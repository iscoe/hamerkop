import abc
import collections


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
