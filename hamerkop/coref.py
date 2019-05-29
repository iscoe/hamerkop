from abc import ABC, abstractmethod


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
        document.mention_chains = [[mention] for mention in document.mentions]
        return document
