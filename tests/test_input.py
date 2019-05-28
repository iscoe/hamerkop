import os
import unittest
from hamerkop.input import *
from hamerkop.core import EntityType
from hamerkop.utilities import InProcessIncremental


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class CoNLLReaderTest(unittest.TestCase):

    def test_simple(self):
        filename = get_filename('data/conll/conll_reader_test_no_header')
        data = [x for x in conll_reader(filename)]
        self.assertEqual(2, len(data))
        self.assertEqual(9, len(data[0]))
        self.assertEqual(6, len(data[1]))
        self.assertEqual('George', data[0][0].token)
        self.assertEqual('B-LOC', data[0][8].tag)
        self.assertEqual('IL5_DF_020521_20170505_H0040MWIB', data[0][1].docid)
        self.assertEqual((19, 21), data[0][5].offsets)

    def test_with_header(self):
        filename = get_filename('data/conll/conll_reader_test_header')
        with self.assertRaises(CoNLLReaderException) as context:
            gen = conll_reader(filename)
            next(gen)

    def test_with_missing_file(self):
        filename = get_filename('data/conll/conll_reader_test_not_exist')
        with self.assertRaises(CoNLLReaderException) as context:
            data = [x for x in conll_reader(filename)]


class DocumentPreparerTest(unittest.TestCase):

    def test_with_consecutive_b_tags(self):
        preparer = DocumentPreparer(InProcessIncremental())
        rows = [
            Row('George', 'B-PER', 'doc1', (0, 6)),
            Row('Tony', 'B-PER', 'doc1', (8, 12)),
            Row('are', 'O', 'doc1', (13, 15)),
            Row('crazy', 'O', 'doc1', (16, 18)),
        ]
        doc = preparer.process(rows)
        self.assertEqual(2, len(doc.mentions))
        self.assertEqual(4, len(doc.tokens))
        self.assertEqual((0, 6), doc.mentions[0].offsets)
        self.assertEqual((0, 0), doc.mentions[0].token_offsets)
        self.assertEqual('George', ' '.join(doc.tokens[doc.mentions[0].token_offsets[0]:doc.mentions[0].token_offsets[1]+1]))
        self.assertEqual('Tony', ' '.join(doc.tokens[doc.mentions[1].token_offsets[0]:doc.mentions[1].token_offsets[1]+1]))
        self.assertEqual('doc1', doc.mentions[1].docid)
        self.assertEqual('doc1', doc.docid)
        self.assertEqual((1, 1), doc.mentions[1].token_offsets)
        self.assertEqual(EntityType.PER, doc.mentions[1].type)

    def test_with_ending_i_tag(self):
        preparer = DocumentPreparer(InProcessIncremental())
        rows = [
            Row('Here', 'O', 'doc1', (0, 4)),
            Row('are', 'O', 'doc1', (5, 8)),
            Row('the', 'O', 'doc1', (9, 12)),
            Row('Thomas', 'B-PER', 'doc1', (13, 18)),
            Row('Jefferson', 'I-PER', 'doc1', (19, 28)),
        ]
        doc = preparer.process(rows)
        self.assertEqual(1, len(doc.mentions))
        self.assertEqual(5, len(doc.tokens))
        self.assertEqual('doc1', doc.docid)
        self.assertEqual('Thomas Jefferson', doc.mentions[0].string)
        self.assertEqual((3,4), doc.mentions[0].token_offsets)
        self.assertEqual('Thomas Jefferson', ' '.join(doc.tokens[doc.mentions[0].token_offsets[0]:doc.mentions[0].token_offsets[1]+1]))


    def test_with_no_tags(self):
        preparer = DocumentPreparer(InProcessIncremental())
        rows = [
            Row('Here', 'O', 'doc1', (0, 4)),
            Row('are', 'O', 'doc1', (5, 8)),
            Row('the', 'O', 'doc1', (9, 12)),
            Row('Thomas', 'O', 'doc1', (13, 18)),
            Row('Jefferson', 'O', 'doc1', (19, 28)),
        ]
        doc = preparer.process(rows)
        self.assertIsNone(doc)
