import io
import os
import unittest
import unittest.mock
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
            self.assertEqual('IL5_DF_020521_20170505_H0040MWIB', data[0][1].doc_id)
            self.assertEqual((19, 21), data[0][5].offsets)

    def test_with_header(self):
        filename = get_filename('data/conll/conll_reader_test_header')
        with open(filename, 'r') as fp, self.assertRaises(CoNLLReaderException) as context:
            gen = read_conll(fp)
            next(gen)


class DocumentPreparerTest(unittest.TestCase):
    def test_with_consecutive_b_tags(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.ENG))
        rows = [
            Row('George', 'B-PER', '_NW_doc1', (0, 6), 0),
            Row('Tony', 'B-PER', '_NW_doc1', (8, 12), 0),
            Row('are', 'O', '_NW_doc1', (13, 15), 0),
            Row('crazy', 'O', '_NW_doc1', (16, 18), 0),
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
        self.assertEqual('_NW_doc1', doc.mentions[1].doc_id)
        self.assertEqual('_NW_doc1', doc.doc_id)
        self.assertEqual((1, 2), doc.mentions[1].token_offsets)
        self.assertEqual(EntityType.PER, doc.mentions[1].type)

    def test_with_ending_i_tag(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.ENG))
        rows = [
            Row('Here', 'O', '_NW_doc1', (0, 4), 0),
            Row('are', 'O', '_NW_doc1', (5, 8), 0),
            Row('the', 'O', '_NW_doc1', (9, 12), 0),
            Row('Thomas', 'B-PER', '_NW_doc1', (13, 18), 0),
            Row('Jefferson', 'I-PER', '_NW_doc1', (19, 28), 0),
        ]
        doc = preparer.process(rows)
        self.assertEqual(1, len(doc.mentions))
        self.assertEqual(5, len(doc.tokens))
        self.assertEqual('_NW_doc1', doc.doc_id)
        self.assertEqual('Thomas Jefferson', doc.mentions[0].string)
        self.assertEqual((3, 5), doc.mentions[0].token_offsets)
        self.assertEqual('Thomas Jefferson',
                         ' '.join(doc.tokens[doc.mentions[0].token_offsets[0]:doc.mentions[0].token_offsets[1]]))

    def test_with_no_tags(self):
        preparer = DocumentPreparer(InProcessIncremental(), FixedLang(Lang.ENG))
        rows = [
            Row('Here', 'O', '_NW_doc1', (0, 4), 0),
            Row('are', 'O', '_NW_doc1', (5, 8), 0),
            Row('the', 'O', '_NW_doc1', (9, 12), 0),
            Row('Thomas', 'O', '_NW_doc1', (13, 18), 0),
            Row('Jefferson', 'O', '_NW_doc1', (19, 28), 0),
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

    def test_with_no_tags(self):
        filename = get_filename('data/conll/conll_reader_test_no_header_no_tags')
        with open(filename, 'r') as fp:
            reader = InputReader(fp)
            docs = list(reader)
            self.assertEqual(0, len(docs))


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
        doc = Document(chains[0].mentions + chains[1].mentions, [], Lang.ENG)
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
        self.assertEqual(0, len(diane.links))
        self.assertEqual('NILC90696', diane.cluster_id)


class EntityCreatorTest(unittest.TestCase):
    def test(self):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        with open(entities_filename, 'r') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            next(reader)
            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertEqual('1', entity.id)
            self.assertEqual(EntityType.GPE, entity.type)
            self.assertEqual(EntityOrigin.GEO, entity.origin)
            self.assertEqual('New York City', entity.name)
            self.assertIsInstance(entity.context, GeoContext)
            self.assertAlmostEqual(42.6499, entity.context.latitude)
            self.assertAlmostEqual(11.53335, entity.context.longitude)
            self.assertEqual('US', entity.context.country)
            self.assertEqual(999, entity.context.population)
            self.assertEqual(2, len(entity.urls))

            row = next(reader)
            entity = EntityCreator.create(row)
            self.assertEqual('2', entity.id)
            self.assertEqual(0, len(entity.urls))
            self.assertIsNone(entity.context)

            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertIsInstance(entity.context, PerContext)
            self.assertEqual('Boston', entity.context.location)
            self.assertEqual(['President', 'Vice President'], entity.context.titles)
            self.assertEqual(['USA'], entity.context.organizations)

            row = next(reader)
            entity = EntityCreator.create(row)
            self.assertEqual('11', entity.id)

            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertEqual('17', entity.id)
            self.assertEqual(EntityType.ORG, entity.type)
            self.assertEqual(EntityOrigin.APB, entity.origin)
            self.assertEqual('UNICEF', entity.name)
            self.assertIsInstance(entity.context, OrgContext)
            self.assertEqual('New York City', entity.context.location)


class CascadeNameFilterTest(unittest.TestCase):
    def getFilter(self, return_value):
        f = unittest.mock.Mock()
        f.filter = unittest.mock.Mock(return_value=return_value)
        return f

    def testTrueFalse(self):
        f1 = self.getFilter(True)
        f2 = self.getFilter(False)
        nf = CascadeNameFilter([f1, f2])
        self.assertTrue(nf.filter('test'))

    def testFalseTrue(self):
        f1 = self.getFilter(False)
        f2 = self.getFilter(True)
        nf = CascadeNameFilter([f1, f2])
        self.assertTrue(not nf.filter('test'))

    def testNoneTrue(self):
        f1 = self.getFilter(None)
        f2 = self.getFilter(True)
        nf = CascadeNameFilter([f1, f2])
        self.assertTrue(nf.filter('test'))

    def testNone(self):
        f1 = self.getFilter(None)
        f2 = self.getFilter(None)
        nf = CascadeNameFilter([f1, f2])
        self.assertTrue(not nf.filter('test'))


class LanguageBasedNameFilterTest(unittest.TestCase):
    def get_buffer(self, data):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zfp:
            zfp.writestr(LanguageBasedNameFilter.ALT_NAMES_FILE, data)
        return buffer

    def test_same_string(self):
        buffer = self.get_buffer(
            "0\t0\tfr\tFrance\n"
            "0\t0\ten\tFrance\n"
            "0\t0\ten\tParis\n"
            "0\t0\tfr\tParis\n"
        )
        nf = LanguageBasedNameFilter(buffer, 'de')
        self.assertTrue(nf.filter('france'))
        self.assertTrue(nf.filter('Paris'))

    def test_missing_string(self):
        buffer = self.get_buffer(
            "0\t0\tfr\tFrance\n"
        )
        nf = LanguageBasedNameFilter(buffer, 'de')
        self.assertTrue(nf.filter('New York'))

    def test_not_lang(self):
        buffer = self.get_buffer(
            "0\t0\tfr\tFrance\n"
            "0\t0\tde\tBerlin\n"
        )
        nf = LanguageBasedNameFilter(buffer, 'de')
        self.assertTrue(not nf.filter('France'))
        self.assertTrue(nf.filter('Berlin'))

    def test_empty_string(self):
        buffer = self.get_buffer(
            "0\t0\t\tFrance\n"
        )
        nf = LanguageBasedNameFilter(buffer, 'de')
        self.assertTrue(nf.filter('France'))
