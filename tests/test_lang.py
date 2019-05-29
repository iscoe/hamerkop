import os
import unittest
from hamerkop.lang import *


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def read_file(filename):
    with open(filename, 'r') as fp:
        return fp.read()


def tokenize(string):
    return string.split()


class LangTest(unittest.TestCase):
    def test_from_code(self):
        self.assertEqual(Lang.AM, Lang.from_code('AM'))
        self.assertEqual(Lang.AM, Lang.from_code('am'))

    def test_from_code_invalid(self):
        self.assertIsNone(Lang.from_code('ZZ'))


class NgramLangDetectorTest(unittest.TestCase):
    DATA = {
        Lang.EN: tokenize(read_file(get_filename('data/lang_id/en.txt'))),
        Lang.ZH: tokenize(read_file(get_filename('data/lang_id/zh.txt'))),
    }

    def test(self):
        detector = NgramLangDetector()
        self.assertEqual(Lang.EN, detector.detect('file1', self.DATA[Lang.EN]))
        self.assertEqual(Lang.ZH, detector.detect('file2', self.DATA[Lang.ZH]))

    def test_without_data(self):
        detector = NgramLangDetector()
        self.assertIsNone(detector.detect('file3', []))
