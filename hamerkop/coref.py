import abc
import logging

from .core import EntityType, MentionChain
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class CoRef(abc.ABC):
    """
    Within Document Coreference

    Turns mentions into mention chains
    """
    @abc.abstractmethod
    def coref(self, document):
        """
        Process the mentions in a document to create mention chains
        :param document: Document
        """
        pass


class CoRefUpdate(abc.ABC):
    """
    Update the current mention chains (split or merge)
    """
    @abc.abstractmethod
    def update(self, document):
        """
        Process the current mention chains to merge or split some
        :param document: Document
        """
        pass

    def merge(self, chains, *to_merge):
        logger.debug('{} merging {}'.format(self.__class__.__name__, to_merge))
        new_chain = MentionChain(sum([chain.mentions for chain in to_merge], []))
        chains = [x for x in chains if x not in to_merge]
        chains.append(new_chain)
        return chains


class TwoStageCoRef(CoRef):
    """
    Create mention chains with a CoRef component and then update with one or more CoRefUpdate components
    """
    def __init__(self, coref, updaters):
        self._coref = coref
        self._updaters = updaters

    def coref(self, document):
        self._coref.coref(document)
        for updater in self._updaters:
            updater.update(document)


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


class CoRefAcronymUpdate(CoRefUpdate):
    """
    Finds best match for names that look like acronyms

    This only works for scripts that support case.
    This does not handle words that are dropped like 'of'.
    """
    def __init__(self, min_length):
        """
        :param min_length: Minimum length in characters
        """
        self.min_length = min_length

    def update(self, document):
        acronym_chains = [chain for chain in document.mention_chains if self.is_acronym(chain.name)]
        if acronym_chains:
            other_chains = [(chain, self.create_acronym(chain.name)) for chain in document.mention_chains
                            if chain not in acronym_chains]
            for acronym_chain in acronym_chains:
                matches = []
                for chain, acronym in other_chains:
                    if acronym_chain.type != chain.type:
                        continue
                    if acronym_chain.name == acronym:
                        matches.append(chain)
                if matches:
                    matches = self.rank(acronym_chain, matches)
                    document.mention_chains = self.merge(document.mention_chains, acronym_chain, matches[0])

    @staticmethod
    def rank(acronym_chain, matches):
        # TODO for now default to first instance
        return matches

    def is_acronym(self, string):
        if len(string) < self.min_length:
            return False
        return string.upper() == string

    @staticmethod
    def create_acronym(string):
        return ''.join(word[0].upper() for word in string.split())
