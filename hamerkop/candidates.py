from abc import ABC, abstractmethod
import faker

from .core import Entity, EntityOrigin, EntityType


class CandidateGenerator(ABC):
    """
    A candidate generator finds reasonable candidates for a mention.
    """

    @abstractmethod
    def find(self, document):
        """
        Find candidates
        :param document: Document with mention chains
        :return: Document with added candidates on the mention chains
        """
        pass


class NullGenerator(CandidateGenerator):
    """Always returns no candidates"""
    def find(self, document):
        for chain in document.mention_chains:
            chain.candidates = []
        return document


class MockGenerator(CandidateGenerator):
    """Create fake candidates to support various kinds of testing"""
    def __init__(self, num):
        self.num = num
        self.faker = faker.Faker()

    def find(self, document):
        for chain in document.mention_chains:
            chain.candidates = []
            for x in range(self.num):
                if chain.type == EntityType.PER:
                    entity = Entity(self.faker.ssn(), EntityType.PER, self.faker.name(), EntityOrigin.WLL)
                elif chain.type == EntityType.ORG:
                    entity = Entity(self.faker.ssn(), EntityType.ORG, self.faker.company(), EntityOrigin.APB)
                else:
                    loc = self.faker.local_latlng(country_code="US", coords_only=False)
                    entity = Entity(self.faker.ssn(), chain.type, loc[2], EntityOrigin.GEO)
                chain.candidates.append(entity)
        return document
