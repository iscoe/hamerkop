import re
import string
import sys
import unicodedata


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
