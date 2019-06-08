import collections
import unittest
from hamerkop.string import *


TestCase = collections.namedtuple('TextCase', 'input expect')


class StringUtilTest(unittest.TestCase):
    def test_remove_punct(self):
        test_cases = [
            TestCase('this-is_a#test.', 'thisisatest')
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.remove_punct(test_case.input))

    def test_replace_punct(self):
        test_cases = [
            TestCase('this-is_a#test.', 'this is a test')
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.replace_punct(test_case.input))

    def test_remove_unicode_punct(self):
        test_cases = [
            TestCase('this-is_a#test.', 'thisisatest'),
            TestCase('ብሓሙስ ሰነ ፡ ሓለዋ።', 'ብሓሙስ ሰነ  ሓለዋ'),
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.remove_unicode_punct(test_case.input))

    def test_replace_unicode_punct(self):
        test_cases = [
            TestCase('this-is_a#test.', 'this is a test'),
            TestCase('ብሓሙስ ሰነ ፡ ሓለዋ።', 'ብሓሙስ ሰነ   ሓለዋ'),
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.replace_unicode_punct(test_case.input))

    def test_remove_emojis(self):
        test_cases = [
            TestCase('great job 👍', 'great job ')
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.remove_emojis(test_case.input))

    def test_remove_double_letter(self):
        test_cases = [
            TestCase('raatiffii', 'ratifi'),
            TestCase('this is a testt', 'this is a test'),
        ]
        for test_case in test_cases:
            self.assertEqual(test_case.expect, String.remove_double_letter(test_case.input))
