from abc import ABCMeta, abstractmethod
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


class Identifier(object):
    """Abstract base class for creating unique identifiers"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def assign(self, mention):
        """
        Assign an identifier to a mention
        :param mention: EntityMention
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
