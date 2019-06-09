import io
import os
import unittest
from hamerkop.io import *
from hamerkop.core import Document, Entity, EntityOrigin, EntityType, Mention, MentionChain
from hamerkop.lang import Lang, FixedLang
from hamerkop.utilities import InProcessIncremental


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class ReadCoNLLTest(unittest.TestCase):
    def test_simple(self):
        filename = get_filename('data/conll/conll_reader_test_no_header')
        with open(filename, 'r') as fp:
            data = [x for x in read_conll(fp)]
            self.assertEqual(2, len(data))
            self.assertEqual(9, len(data[0]))
            self.assertEqual(6, len(data[1]))
            self.assertEqual('George', data[0][0].token)
            self.assertEqual('B-LOC', data[0][8].tag)
            self.assertEqual('IL5_DF_020521_20170505_H0040MWIB', data[0][1].docid)
            self.assertEqual((19, 21), data[0][5].offsets)

    def test_with_header(self):
        filename = get_filename('data/conll/conll_reader_test_header')
        with open(filename, 'r') as fp, self.assertRaises(CoNLLReaderException) as context:
            gen = read_conll(fp)
            next(gen)


class DocumentPreparerTest(unittest.TestCase):
    def test_with_consecutive_b_tags(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.EN))
        rows = [
            Row('George', 'B-PER', '_NW_doc1', (0, 6)),
            Row('Tony', 'B-PER', '_NW_doc1', (8, 12)),
            Row('are', 'O', '_NW_doc1', (13, 15)),
            Row('crazy', 'O', '_NW_doc1', (16, 18)),
        ]
        doc = preparer.process(rows)
        self.assertEqual(2, len(doc.mentions))
        self.assertEqual(4, len(doc.tokens))
        self.assertEqual((0, 6), doc.mentions[0].offsets)
        self.assertEqual((0, 1), doc.mentions[0].token_offsets)
        self.assertEqual('George',
                         ' '.join(doc.tokens[doc.mentions[0].token_offsets[0]:doc.mentions[0].token_offsets[1]]))
        self.assertEqual('Tony',
                         ' '.join(doc.tokens[doc.mentions[1].token_offsets[0]:doc.mentions[1].token_offsets[1]]))
        self.assertEqual('_NW_doc1', doc.mentions[1].docid)
        self.assertEqual('_NW_doc1', doc.docid)
        self.assertEqual((1, 2), doc.mentions[1].token_offsets)
        self.assertEqual(EntityType.PER, doc.mentions[1].type)

    def test_with_ending_i_tag(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.EN))
        rows = [
            Row('Here', 'O', '_NW_doc1', (0, 4)),
            Row('are', 'O', '_NW_doc1', (5, 8)),
            Row('the', 'O', '_NW_doc1', (9, 12)),
            Row('Thomas', 'B-PER', '_NW_doc1', (13, 18)),
            Row('Jefferson', 'I-PER', '_NW_doc1', (19, 28)),
        ]
        doc = preparer.process(rows)
        self.assertEqual(1, len(doc.mentions))
        self.assertEqual(5, len(doc.tokens))
        self.assertEqual('_NW_doc1', doc.docid)
        self.assertEqual('Thomas Jefferson', doc.mentions[0].string)
        self.assertEqual((3, 5), doc.mentions[0].token_offsets)
        self.assertEqual('Thomas Jefferson',
                         ' '.join(doc.tokens[doc.mentions[0].token_offsets[0]:doc.mentions[0].token_offsets[1]]))

    def test_with_no_tags(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.EN))
        rows = [
            Row('Here', 'O', '_NW_doc1', (0, 4)),
            Row('are', 'O', '_NW_doc1', (5, 8)),
            Row('the', 'O', '_NW_doc1', (9, 12)),
            Row('Thomas', 'O', '_NW_doc1', (13, 18)),
            Row('Jefferson', 'O', '_NW_doc1', (19, 28)),
        ]
        doc = preparer.process(rows)
        self.assertIsNone(doc)


class InputReaderTest(unittest.TestCase):
    def test(self):
        filename = get_filename('data/conll/conll_reader_test_no_header')
        with open(filename, 'r') as fp:
            reader = InputReader(fp)
            docs = list(reader)
            self.assertEqual(2, len(docs))


class OutputWriterTest(unittest.TestCase):
    def test(self):
        chains = [
            MentionChain([
                Mention('Henry', '_WL_doc34', (123, 128), (17, 17), EntityType.PER, 'Men1')
            ]),
            MentionChain([
                Mention('Ed Smith', '_WL_doc34', (141, 149), (22, 23), EntityType.PER, 'Men2'),
                Mention('Ed', '_WL_doc34', (197, 199), (44, 44), EntityType.PER, 'Men3')
            ])
        ]
        chains[0].entity = Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)
        chains[1].entity = None
        doc = Document(chains[0].mentions + chains[1].mentions, [], Lang.EN)
        doc.mention_chains = chains

        buffer = io.StringIO()
        writer = OutputWriter(buffer, 'test', 0.75)
        writer.write(doc)

        buffer.seek(0)
        lines = buffer.readlines()
        line1 = "test\tMen1\tHenry\t_WL_doc34:123-128\t67\tPER\tNAM\t0.75"
        self.assertEqual(line1, lines[0].strip())


class OutputReaderTest(unittest.TestCase):
    def test(self):
        filename = get_filename('data/output/ground_truth.tab')
        with open(filename, 'r') as fp:
            data = OutputReader.read(fp)
        self.assertEqual(4, len(data))

        paris = data['IL9_NW_020583_20180425_I0040RHG9'][(1620, 1624)]
        self.assertEqual(EntityType.GPE, paris.entity_type)
        self.assertEqual(LinkType.LINK, paris.link_type)
        self.assertEqual('2988507', paris.links[0])

        congo = data['IL9_NW_020595_20171201_I0040RCHV'][(180, 184)]
        self.assertEqual(EntityType.GPE, congo.entity_type)
        self.assertEqual(LinkType.LINK, congo.link_type)
        self.assertEqual(3, len(congo.links))
        self.assertEqual('203312', congo.links[0])

        diane = data['IL9_WL_020632_20171020_I0040S56W'][(1633, 1637)]
        self.assertEqual(EntityType.PER, diane.entity_type)
        self.assertEqual(LinkType.NIL, diane.link_type)