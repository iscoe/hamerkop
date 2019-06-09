import abc

from .core import EntityType, MentionChain
from .utilities import CaseInsensitiveDict


class CoRef(abc.ABC):
    """
    Indoc Coreference to create mention chains
    """

    @abc.abstractmethod
    def coref(self, document):
        """
        Process the mentions in a document to create mention chains
        :param document: Document
        """
        pass


class UnchainedCoRef(CoRef):
    """
    Each mention gets its own chain
    """
    def coref(self, document):
        document.mention_chains = [MentionChain([mention]) for mention in document.mentions]


class ExactMatchCoRef(CoRef):
    """
    Mentions strings that are exact matches are chained (case not considered)
    """
    def coref(self, document):
        chain_data = {}
        for entity_type in EntityType.TYPES:
            chain_data[entity_type] = CaseInsensitiveDict()
        for mention in document.mentions:
            if mention.string not in chain_data[mention.type]:
                chain_data[mention.type][mention.string] = []
            chain_data[mention.type][mention.string].append(mention)
        document.mention_chains = []
        for entity_type in chain_data:
            chains = [MentionChain(chain) for chain in chain_data[entity_type].values()]
            document.mention_chains.extend(chains)
