import unittest
from hamerkop.core import Document, EntityType, Mention, MentionChain
from hamerkop.coref import *
from hamerkop.lang import Lang


class CoRefUpdateTest(unittest.TestCase):
    class DummyMerger(CoRefUpdate):
        def update(self, document):
            pass

    def test_merge(self):
        chains = [
            MentionChain([
                Mention('1', '_NW_1', (), (), EntityType.PER, 'Men1'),
                Mention('4', '_NW_1', (), (), EntityType.PER, 'Men4')
            ]),
            MentionChain([Mention('2', '_NW_1', (), (), EntityType.PER, 'Men2')]),
            MentionChain([Mention('3', '_NW_1', (), (), EntityType.PER, 'Men3')]),
        ]
        updater = CoRefUpdateTest.DummyMerger()
        chains = updater.merge(chains, chains[0], chains[2])
        self.assertEqual(2, len(chains))
        self.assertEqual(3, len(chains[-1].mentions))


class UnchainedCoRefTest(unittest.TestCase):
    def test(self):
        doc = Document([
            Mention('Ed Smith', '_DF_doc34', (141, 149), (22, 23), EntityType.PER, 'Men1'),
            Mention('Ed Smith', '_DF_doc34', (146, 154), (24, 25), EntityType.PER, 'Men2'),
            Mention('Ben Smith', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3'),
        ], [], Lang.EN)
        coref = UnchainedCoRef()
        coref.coref(doc)

        self.assertEqual(3, len(doc.mention_chains))


class ExactMatchCoRefTest(unittest.TestCase):
    def test(self):
        doc = Document([
            Mention('Ed Smith', '_DF_doc34', (141, 149), (22, 23), EntityType.PER, 'Men1'),
            Mention('Ed Smith', '_DF_doc34', (146, 154), (24, 25), EntityType.PER, 'Men2'),
            Mention('Ben Smith', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3'),
            Mention('ed Smith', '_DF_doc34', (186, 194), (51, 52), EntityType.PER, 'Men4'),
            Mention('Ed Smith', '_DF_doc34', (237, 245), (71, 72), EntityType.ORG, 'Men5'),
        ], [], Lang.EN)
        coref = ExactMatchCoRef()
        coref.coref(doc)

        self.assertEqual(3, len(doc.mention_chains))
        self.assertEqual(sorted([1, 1, 3]), sorted(list(map(len, doc.mention_chains))))


class CoRefAcronymUpdateTest(unittest.TestCase):
    def test_create_acronym(self):
        self.assertEqual('SC', CoRefAcronymUpdate.create_acronym('south carolina'))
        self.assertEqual('M', CoRefAcronymUpdate.create_acronym('Maryland'))

    def test_is_acronym(self):
        updater = CoRefAcronymUpdate(3)
        self.assertTrue(updater.is_acronym('USA'))
        self.assertTrue(updater.is_acronym('UNCHR'))
        self.assertFalse(updater.is_acronym('LoReHLT'))
        self.assertFalse(updater.is_acronym('US'))

    def test_is_acronym2(self):
        doc = Document([
            Mention('South Carolina', '_DF_doc34', (141, 149), (22, 23), EntityType.GPE, 'Men1'),
            Mention('SC', '_DF_doc34', (146, 154), (24, 25), EntityType.GPE, 'Men2'),
            Mention('south carolina', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3'),
            Mention('ed Smith', '_DF_doc34', (186, 194), (51, 52), EntityType.PER, 'Men4'),
            Mention('Ed Smith', '_DF_doc34', (237, 245), (71, 72), EntityType.ORG, 'Men5'),
        ], [], Lang.EN)
        doc.mention_chains = [
            MentionChain([doc.mentions[0]]),
            MentionChain([doc.mentions[1]]),
            MentionChain([doc.mentions[2]]),
            MentionChain([doc.mentions[3], doc.mentions[4]]),
        ]
        updater = CoRefAcronymUpdate(2)
        updater.update(doc)
        self.assertEqual(3, len(doc.mention_chains))
