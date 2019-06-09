import abc
import collections
import contextlib
import functools
import inspect
import logging
import re

from .core import DocType, EntityType
from .string import String
from .utilities import CaseInsensitiveDict, CaseInsensitiveSet

logger = logging.getLogger(__name__)


class Preprocessor(abc.ABC):
    """
    A preprocessor runs before coref and candidate generation to filter and clean the mentions.
    """

    @abc.abstractmethod
    def process(self, document):
        """
        Process the mentions in a document
        :param document: Document
        """
        pass


def pcm():
    """Convenience function for Preprocessor Context Manager"""
    return PreprocessorReporter.get()


class ReportProperty(type):
    """
    Metaclass that adds a report class property

    Note that implementers must have a get() classmethod
    """
    @property
    def report(cls):
        return cls.get()._report


class PreprocessorReporter(metaclass=ReportProperty):
    """
    Reporter for Preprocessor components

    Records:
    * mention modifications
    * mention removals
    """
    instance = None

    def __init__(self):
        self._report = {
            'modifications': collections.Counter(),
            'removals': collections.Counter(),
        }
        self.disable()

    def enable(self):
        self.modification = self.modification_debug
        self.removal = self.removal_debug

    def disable(self):
        self.modification = self.modification_production
        self.removal = self.removal_production

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = PreprocessorReporter()
        return cls.instance

    @classmethod
    def activate(cls):
        cls.get().enable()

    @classmethod
    def deactivate(cls):
        cls.get().disable()

    @contextlib.contextmanager
    def modification(self, mention):
        yield

    @contextlib.contextmanager
    def modification_production(self, mention):
        yield

    @contextlib.contextmanager
    def modification_debug(self, mention):
        caller = self.get_caller()
        original = mention.string
        yield
        if original != mention.string:
            self._report['modifications'].update({caller: 1})

    @contextlib.contextmanager
    def removal(self, document):
        yield

    @contextlib.contextmanager
    def removal_production(self, document):
        yield

    @contextlib.contextmanager
    def removal_debug(self, document):
        caller = self.get_caller()
        original_size = len(document.mentions)
        yield
        if original_size != len(document.mentions):
            num = original_size - len(document.mentions)
            self._report['removals'].update({caller: num})

    @staticmethod
    def get_caller():
        # 1=self, 2=contextlib, 3=caller
        return inspect.stack()[3][0].f_locals['self'].__class__.__name__


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
        with pcm().removal(document):
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
            with pcm().modification(mention):
                mention.string = mention.string.translate(self.trans_table)
                mention.string = String.remove_emojis(mention.string)


class GarbageRemover(Preprocessor):
    """
    Removes garbage mentions
    * removes website urls
    * empty mention strings (can be caused by other preprocessors)
    """
    def process(self, document):
        with pcm().removal(document):
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
        with pcm().removal(document):
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
        with pcm().removal(document):
            document.mentions = [mention for mention in document.mentions if mention.string not in self.data]


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
            with pcm().modification(mention):
                if mention.string in self.map:
                    mention.string = self.map[mention.string]


class NameTranslator(Preprocessor):
    """
    Translates or transliterates name strings.

    Stores previous string on mention as native_string
    TODO: check for code switching and not run on English strings?
    """
    def __init__(self, translator):
        """
        :param translator: Translator object
        """
        self.translator = translator

    def process(self, document):
        for mention in document.mentions:
            with pcm().modification(mention):
                translation = self.translator.translate(mention.string, document.lang)
                if translation and translation != mention.string:
                    mention.native_string = mention.string
                    mention.string = translation


class NameStemmer(Preprocessor):
    """
    Replaces tokens of name string with stems.
    TODO: does not handle punctuation (dashes, apostrophes, parentheses)
    """
    def __init__(self, stemmer):
        """
        :param stemmer: Stemmer object
        """
        self.stemmer = stemmer

    def process(self, document):
        for mention in document.mentions:
            with pcm().modification(mention):
                words = mention.string.split()
                words = list(map(functools.partial(self.stemmer.stem, lang=document.lang), words))
                mention.string = ' '.join(words)


class TwitterUsernameReplacer(Preprocessor):
    """
    Replaces twitter @username with screen name
    The @username is still available as original_string on the mention.
    The username map is username -> screen name
    For example: nytimes   New York Times
    """
    # TODO case sensitive and not handling multi-token phrase with username in it
    def __init__(self, username_map):
        self.map = username_map

    def process(self, document):
        # only process tweets
        if document.type != DocType.SN:
            return
        for mention in document.mentions:
            with pcm().modification(mention):
                if mention.string and mention.string[0] == '@':
                    s = mention.string[1:]
                    s = String.remove_emojis(s)
                    # chop punctuation off end of username
                    if s and not (s[-1].isalpha() or s[-1].isdigit() or s[-1] == '_'):
                        s = s[:-1]
                    if s in self.map:
                        mention.string = self.map[s]


class TwitterHashtagProcessor(Preprocessor):
    """
    Replaces twitter #HashTag as Hash Tag
    The #HashTag is still available as original_string on the mention.
    """
    def __init__(self):
        # TODO this does not handle numbers and leaves behind empty matches
        self.hashtag_regex = re.compile('[A-Z]*[a-z]*')

    def process(self, document):
        for mention in document.mentions:
            with pcm().modification(mention):
                if mention.string and mention.string[0] == '#':
                    mention.string = mention.string[1:]
                    matches = re.findall(self.hashtag_regex, mention.string)
                    if matches:
                        matches = [match for match in matches if match]
                        s = ' '.join(matches)
                        # TODO find a better approach for bad strings - like removing the mention
                        if s:
                            mention.string = s
