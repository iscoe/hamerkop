from abc import ABC, abstractmethod

from .core import MentionChain


class CoRef(ABC):
    """
    Indoc Coreference to create mention chains
    """

    @abstractmethod
    def coref(self, document):
        """
        Process the mentions in a document to create mention chains
        :param document: Document
        :return: Document
        """
        pass


class UnchainedCoRef(CoRef):
    """
    Each mention gets its own chain
    """
    def coref(self, document):
        document.mention_chains = [MentionChain([mention]) for mention in document.mentions]
        return document
