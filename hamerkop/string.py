# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import functools
import re
import string
import subprocess
import sys
import unicodedata

from .lang import Lang
from .utilities import CaseInsensitiveDict


class String:
    """
    Collection of string utilities
    """
    PUNCT_TABLE = str.maketrans('', '', string.punctuation)
    PUNCT_SPACE_TABLE = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    UNICODE_PUNCT_STR = ''.join([chr(i) for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith('P')])
    UNICODE_PUNCT_TABLE = str.maketrans('', '', UNICODE_PUNCT_STR)
    UNICODE_PUNCT_SPACE_TABLE = str.maketrans(UNICODE_PUNCT_STR, ' ' * len(UNICODE_PUNCT_STR))
    EMOJI_REGEX = re.compile(r'['
                             '\U0001F170-\U0001F19A'  # buttons
                             '\U0001F200-\U0001F235'  # japanese buttons
                             '\U0001F300-\U0001F5FF'  # symbols & pictographs
                             '\U0001F600-\U0001F64F'  # emoticons
                             '\U0001F680-\U0001F6FF'  # transport & map symbols
                             '\U0001F1E0-\U0001F1FF'  # flags
                             '\U0001F900-\U0001F9FF'  # faces added in unicode 8
                             ']+')

    @classmethod
    def remove_punct(cls, str):
        """Removes ASCII punctuation"""
        return str.translate(cls.PUNCT_TABLE)

    @classmethod
    def replace_punct(cls, str):
        """Replaces ASCII punctuation with spaces"""
        return str.translate(cls.PUNCT_SPACE_TABLE).strip()

    @classmethod
    def remove_unicode_punct(cls, str):
        """Removes Unicode punctuation"""
        return str.translate(cls.UNICODE_PUNCT_TABLE)

    @classmethod
    def replace_unicode_punct(cls, str):
        """Replaces Unicode punctuation with spaces"""
        return str.translate(cls.UNICODE_PUNCT_SPACE_TABLE).strip()

    @classmethod
    def remove_emojis(cls, str):
        """Removes emoji characters"""
        return re.sub(cls.EMOJI_REGEX, '', str)

    @staticmethod
    def single_space(str):
        """Replace any sequence of whitespace with a single space"""
        return re.sub('\s+', ' ', str)

    @staticmethod
    def remove_double_letter(str):
        """Remove the second letter of double letters"""
        return re.sub(r'([a-zA-Z])\1+', r'\1', str)

    @staticmethod
    def ngrams(s, n=2):
        """Get a list of ngrams from a string"""
        return [s[i:i + n] for i in range(len(s) - n + 1)]


class Translator(abc.ABC):
    """Translate into English"""
    @abc.abstractmethod
    def translate(self, s, lang):
        """
        Translate the string

        Can return None if no translation is available
        :param s: string to be translated
        :param lang: Lang code
        :return: string in latin characters
        """
        pass


class DictTranslator(Translator):
    """
    Use a dictionary of source -> destination translations.
    Does not do partial translations, only full strings
    """
    def __init__(self, trans_map):
        self.map = CaseInsensitiveDict(trans_map)

    def translate(self, s, lang):
        if s in self.map:
            return self.map[s]


class TranslatorMemoryCache(Translator):
    """
    LRU Memory cache for translations
    """
    def __init__(self, translator, size=1000):
        self.translator = translator
        self.translate = functools.lru_cache(maxsize=size)(self.translate)

    def translate(self, s, lang):
        return self.translator.translate(s, lang)


class TranslatorPersistentCache(Translator):
    """
    Persistent cache for translations
    """
    def __init__(self, translator, cache):
        self.translator = translator
        self.cache = cache

    def translate(self, s, lang):
        if s in self.cache:
            return self.cache[s]
        else:
            t = self.translator.translate(s, lang)
            if t:
                self.cache[s] = t
            return t


class URoman(Translator):
    """
    Transliterate non-English (non-Latin character) strings.

    Uses Ulf Hermjakob's uroman, a universal romanizer.
    The uroman script is written in Perl.
    """
    def __init__(self, uroman_path):
        self.uroman_path = uroman_path

    def translate(self, s, lang):
        if lang == Lang.ENG:
            return
        # ascii strings do not need transliteration
        if all(ord(char) < 128 for char in s):
            return
        ps = subprocess.Popen(('echo', '-n', s), stdout=subprocess.PIPE, universal_newlines=True)
        output = subprocess.check_output(self.uroman_path, stdin=ps.stdout, universal_newlines=True)
        ps.wait()
        # work around for uroman adding a newline
        return output.strip()


class Stemmer(abc.ABC):
    """Produce stem or lemma for a word"""
    @abc.abstractmethod
    def stem(self, string, lang):
        """
        Stem the input string
        :param string: string to be stemmed
        :param lang: Lang code
        :return: string
        """
        pass


class DictStemmer(Stemmer):
    """Use a dictionary of form -> stem"""
    def __init__(self, stem_map):
        self.map = CaseInsensitiveDict(stem_map)

    def stem(self, string, lang):
        if string in self.map:
            return self.map[string]
        else:
            return string
