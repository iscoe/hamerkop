from abc import ABC, abstractmethod


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
    def find(self, document):
        for chain in document.mention_chains:
            chain.candidates = []
        return document
