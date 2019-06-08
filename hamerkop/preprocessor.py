from abc import ABC, abstractmethod
import logging

from .core import EntityType
from .string import String
from .utilities import CaseInsensitiveDict, CaseInsensitiveSet

logger = logging.getLogger(__name__)


class Preprocessor(ABC):
    """
    A preprocessor runs before coref and candidate generation to filter and clean the mentions.
    """

    @abstractmethod
    def process(self, document):
        """
        Process the mentions in a document
        :param document: Document
        """
        pass


class PassThru(Preprocessor):
    """Does not change the entity mentions"""
    def process(self, document):
        pass


class CascadePreprocessor(Preprocessor):
    """Run a list of processors on the mentions"""
    def __init__(self, processors):
        """
        :param processors: list of Preprocessor objects
        """
        self.processors = processors

    def process(self, document):
        for processor in self.processors:
            processor.process(document)


class TypeValidator(Preprocessor):
    """Removes mentions that have unknown types"""
    def process(self, document):
        original_size = len(document.mentions)
        document.mentions = [mention for mention in document.mentions if mention.type in EntityType.TYPES]
        if len(document.mentions) != original_size:
            logger.error("Document {} has an invalid type".format(document.docid))


class TextNormalizer(Preprocessor):
    """
    Normalized text
    * replaces smart quotes and other special punctuation with ascii punct
    * removes emojis
    """
    def __init__(self):
        self.trans_table = str.maketrans("‘’“”—…", "''\"\"-.")

    def process(self, document):
        for mention in document.mentions:
            mention.string = mention.string.translate(self.trans_table)
            mention.string = String.remove_emojis(mention.string)


class GarbageRemover(Preprocessor):
    """
    Removes garbage mentions
    * removes website urls
    * empty mention strings (can be caused by other preprocessors)
    """
    def process(self, document):
        document.mentions = [mention for mention in document.mentions if 'www.' not in mention.string]
        document.mentions = [mention for mention in document.mentions if 'http:' not in mention.string]
        document.mentions = [mention for mention in document.mentions if 'https:' not in mention.string]
        document.mentions = [mention for mention in document.mentions if mention.string]


class FixType(Preprocessor):
    """Fix common type mistakes from NER like al-Qaeda = PER"""
    def __init__(self, type_map):
        """
        :param type_map: dictionary of lowercase name string -> type
        """
        self.map = type_map

    def process(self, document):
        for mention in document.mentions:
            if mention.string.lower() in self.map:
                mention.type = self.map[mention.string.lower()]


class TooLongMentionRemover(Preprocessor):
    """Remove mentions that have too many tokens"""
    def __init__(self, max_tokens=6):
        self.max_tokens = max_tokens

    def process(self, document):
        document.mentions = [mention for mention in document.mentions if self._check(mention)]

    def _check(self, mention):
        """Check if the mention passes the token length test"""
        return mention.string.count(' ') < self.max_tokens


class Blacklist(Preprocessor):
    """Remove mentions that are in a blacklist of common mistakes"""
    def __init__(self, blacklist):
        """
        :param blacklist: list or set of blacklist names
        """
        self.data = CaseInsensitiveSet(blacklist)

    def process(self, document):
        count = len(document.mentions)
        document.mentions = [mention for mention in document.mentions if mention.string not in self.data]
        if len(document.mentions) != count:
            logger.debug("{} mentions removed by blacklist".format(count - len(document.mentions)))


class AcronymReplacer(Preprocessor):
    """
    Uses a map from acronym to entity name
    """
    def __init__(self, acronym_map, ci=False):
        """
        :param acronym_map: dictionary from acronym -> entity name
        :param ci: whether to match the acronym ignoring case
        """
        if ci:
            self.map = CaseInsensitiveDict(acronym_map)
        else:
            self.map = acronym_map

    def process(self, document):
        for mention in document.mentions:
            if mention.string in self.map:
                mention.string = self.map[mention.string]
