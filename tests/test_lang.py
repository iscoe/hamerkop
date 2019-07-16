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
        self.assertEqual(Lang.AMH, Lang.from_code('AMH'))
        self.assertEqual(Lang.AMH, Lang.from_code('amh'))

    def test_from_code_invalid(self):
        self.assertIsNone(Lang.from_code('ZZZ'))


class NgramLangDetectorTest(unittest.TestCase):
    DATA = {
        Lang.ENG: tokenize(read_file(get_filename('data/lang_id/en.txt'))),
        Lang.ZHO: tokenize(read_file(get_filename('data/lang_id/zh.txt'))),
    }

    def test(self):
        detector = NgramLangDetector()
        self.assertEqual(Lang.ENG, detector.detect('file1', self.DATA[Lang.ENG]))
        self.assertEqual(Lang.ZHO, detector.detect('file2', self.DATA[Lang.ZHO]))

    def test_without_data(self):
        detector = NgramLangDetector()
        self.assertIsNone(detector.detect('file3', []))
