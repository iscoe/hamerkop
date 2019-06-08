from abc import ABC, abstractmethod
import faker
import logging

from .core import Entity, EntityOrigin, EntityType

logger = logging.getLogger(__name__)


class CandidateGenerator(ABC):
    """
    A candidate generator finds reasonable candidates for mention chains.
    """

    def process(self, document):
        """
        Process a document of mention chains
        :param document: Document with mention chains
        """
        self.document = document
        for chain in document.mention_chains:
            chain.candidates = self.find(chain)

    @abstractmethod
    def find(self, mention_chain):
        """
        Find candidates for a mention chain
        :param mention_chain: MentionChain object with list of mentions
        :return: List of candidates
        """
        pass


class NullGenerator(CandidateGenerator):
    """Always returns no candidates"""
    def find(self, mention_chain):
        return []


class MockGenerator(CandidateGenerator):
    """Create fake candidates to support various kinds of testing"""
    def __init__(self, num):
        self.num = num
        self.faker = faker.Faker()

    def find(self, mention_chain):
        return [self._create(mention_chain.type) for x in range(self.num)]

    def _create(self, entity_type):
        if entity_type == EntityType.PER:
            entity = Entity(self.faker.ssn(), EntityType.PER, self.faker.name(), EntityOrigin.WLL)
        elif entity_type == EntityType.ORG:
            entity = Entity(self.faker.ssn(), EntityType.ORG, self.faker.company(), EntityOrigin.APB)
        else:
            loc = self.faker.local_latlng(country_code="US", coords_only=False)
            entity = Entity(self.faker.ssn(), entity_type, loc[2], EntityOrigin.GEO)
        return entity


class IndexBasedGenerator(CandidateGenerator):
    """
    Use a NameIndex to find candidates for entity linking.

    Only uses the "best" name from the mention chain.
    """
    def __init__(self, maximum, index):
        self.max = maximum
        self.index = index

    def find(self, mention_chain):
        name = mention_chain.best_name
        candidates = self.index.find(name, mention_chain.type, self.max)
        logger.debug("{}({}): {} candidates from {}".format(
            name, mention_chain.type, len(mention_chain.candidates), type(self.index).__name__))
        return candidates


class CombiningGenerator(CandidateGenerator):
    def __init__(self, generators):
        """
        :param generators: list of CandidateGenerators
        """
        self.generators = generators

    def find(self, mention_chain):
        candidate_dict = {}
        for generator in self.generators:
            for entity in generator.find(mention_chain):
                candidate_dict[entity.id] = entity
        logger.debug("{}({}): {} total candidates".format(mention_chain.string,
                                                          mention_chain.type, len(candidate_dict)))
        return list(candidate_dict.values())


class CachingGenerator(CandidateGenerator):
    """
    Caches candidates based on the mention chain (best name and type).
    This is a memory cache.
    """
    def __init__(self, generator):
        """
        :param generator: CandidateGenerator to cache the results from
        """
        self.generator = generator
        self.cache = {}

    def find(self, mention_chain):
        key = self._gen_key(mention_chain)
        if key in self.cache:
            return self.cache[key]
        candidates = self.generator.find(mention_chain)
        self.cache[key] = candidates
        return candidates

    def _gen_key(self, mention_chain):
        return mention_chain.best_name.string.lower() + ':' + mention_chain.type
