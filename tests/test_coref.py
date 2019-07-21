import unittest
import unittest.mock
from hamerkop.core import Document, EntityType, Link, LinkType, Mention, MentionChain
from hamerkop.coref import *
from hamerkop.lang import Lang


class CorefStageTest(unittest.TestCase):
    class DummyStage(CorefStage):
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
        doc = unittest.mock.Mock()
        doc.mention_chains = chains
        stage = CorefStageTest.DummyStage()
        stage.merge(doc, [chains[0], chains[2]])
        self.assertEqual(2, len(doc.mention_chains))
        self.assertEqual(3, len(doc.mention_chains[-1].mentions))


class CorefScorerTest(unittest.TestCase):
    def test_prepare_gt(self):
        input_gt = {
            'doc1': {
                (0, 1): Link(EntityType.PER, LinkType.LINK, ['123'], None),
                (2, 5): Link(EntityType.PER, LinkType.LINK, ['34', '67'], None),
                (8, 11): Link(EntityType.PER, LinkType.LINK, ['123'], None),
                (14, 17): Link(EntityType.PER, LinkType.LINK, ['34', '67'], None),
                (19, 21): Link(EntityType.PER, LinkType.LINK, ['8'], None),
                (25, 28): Link(EntityType.PER, LinkType.NIL, [], 'NIL01'),
                (32, 38): Link(EntityType.PER, LinkType.NIL, [], 'NIL02'),
                (45, 48): Link(EntityType.PER, LinkType.NIL, [], 'NIL01'),
            },
            'doc2': {
                (4, 8): Link(EntityType.PER, LinkType.LINK, ['123'], None),
            }
        }
        output_gt, _ = CorefScorer._prepare_gt(input_gt)
        self.assertEqual(2, len(output_gt))
        self.assertEqual(5, len(output_gt['doc1']))

    def test_update1(self):
        # first example from table 1 in https://www.aclweb.org/anthology/M95-1005
        gt = {
            'doc1': {
                (0, 1): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (2, 5): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (8, 11): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (14, 17): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
            },
        }
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([
                Mention('1', 'doc1', (0, 1), (), EntityType.PER, 'NIL10'),
                Mention('2', 'doc1', (2, 5), (), EntityType.PER, 'NIL10'),
            ]),
            MentionChain([
                Mention('3', 'doc1', (8, 11), (), EntityType.PER, 'NIL11'),
                Mention('4', 'doc1', (14, 17), (), EntityType.PER, 'NIL11'),
            ]),
        ]
        scorer = CorefScorer(gt, CorefMetric.MUC)
        scorer.update(doc)
        self.assertEqual(2, scorer.recall_numerator)
        self.assertEqual(3, scorer.recall_denominator)
        self.assertEqual(2, scorer.precision_numerator)
        self.assertEqual(2, scorer.precision_denominator)

    def get_example1_test_data(self):
        # first example from "Algorithms for scoring coreference chains"
        gt = {
            'doc1': {
                (0, 1): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (0, 2): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (0, 3): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (0, 4): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (0, 5): Link(EntityType.PER, LinkType.LINK, 'NIL1', None),
                (0, 6): Link(EntityType.PER, LinkType.LINK, 'NIL2', None),
                (0, 7): Link(EntityType.PER, LinkType.LINK, 'NIL2', None),
                (0, 8): Link(EntityType.PER, LinkType.LINK, 'NIL3', None),
                (0, 9): Link(EntityType.PER, LinkType.LINK, 'NIL3', None),
                (0, 10): Link(EntityType.PER, LinkType.LINK, 'NIL3', None),
                (0, 11): Link(EntityType.PER, LinkType.LINK, 'NIL3', None),
                (0, 12): Link(EntityType.PER, LinkType.LINK, 'NIL3', None),
            },
        }
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([
                Mention('1', 'doc1', (0, 1), (), EntityType.PER, 'NIL10'),
                Mention('2', 'doc1', (0, 2), (), EntityType.PER, 'NIL10'),
                Mention('3', 'doc1', (0, 3), (), EntityType.PER, 'NIL10'),
                Mention('4', 'doc1', (0, 4), (), EntityType.PER, 'NIL10'),
                Mention('5', 'doc1', (0, 5), (), EntityType.PER, 'NIL10'),
            ]),
            MentionChain([
                Mention('6', 'doc1', (0, 6), (), EntityType.PER, 'NIL11'),
                Mention('7', 'doc1', (0, 7), (), EntityType.PER, 'NIL11'),
                Mention('8', 'doc1', (0, 8), (), EntityType.PER, 'NIL11'),
                Mention('9', 'doc1', (0, 9), (), EntityType.PER, 'NIL11'),
                Mention('10', 'doc1', (0, 10), (), EntityType.PER, 'NIL11'),
                Mention('11', 'doc1', (0, 11), (), EntityType.PER, 'NIL11'),
                Mention('12', 'doc1', (0, 12), (), EntityType.PER, 'NIL11'),
            ]),
        ]
        return gt, doc

    def test_update2_muc(self):
        gt, doc = self.get_example1_test_data()
        scorer = CorefScorer(gt, CorefMetric.MUC)
        scorer.update(doc)
        self.assertEqual(9, scorer.recall_numerator)
        self.assertEqual(9, scorer.recall_denominator)
        self.assertEqual(9, scorer.precision_numerator)
        self.assertEqual(10, scorer.precision_denominator)

    def test_update2_b3(self):
        gt, doc = self.get_example1_test_data()
        scorer = CorefScorer(gt, CorefMetric.B3)
        scorer.update(doc)
        self.assertEqual(12, scorer.recall_numerator)
        self.assertEqual(12, scorer.recall_denominator)
        self.assertAlmostEqual(0.76, scorer.precision, 2)


class CascadeCorefTest(unittest.TestCase):
    def testWithNoStages(self):
        doc = unittest.mock.Mock()
        doc.mentions = [
            Mention('Ed Smith', '_DF_doc34', (141, 149), (22, 23), EntityType.PER, 'Men1'),
            Mention('Ed Smith', '_DF_doc34', (146, 154), (24, 25), EntityType.PER, 'Men2'),
            Mention('Ben Smith', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3'),
        ]
        coref = CascadeCoref([])
        coref.coref(doc)
        self.assertEqual(3, len(doc.mention_chains))


class ExactMatchStageTest(unittest.TestCase):
    def test(self):
        doc = unittest.mock.Mock()
        doc.mention_chains = [
            MentionChain([Mention('Ed Smith', '_DF_doc34', (141, 149), (22, 23), EntityType.PER, 'Men1')]),
            MentionChain([Mention('Ed Smith', '_DF_doc34', (146, 154), (24, 25), EntityType.PER, 'Men2')]),
            MentionChain([Mention('Ben Smith', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3')]),
            MentionChain([Mention('ed Smith', '_DF_doc34', (186, 194), (51, 52), EntityType.PER, 'Men4')]),
            MentionChain([Mention('Ed Smith', '_DF_doc34', (237, 245), (71, 72), EntityType.ORG, 'Men5')]),
        ]
        stage = ExactMatchStage()
        stage.update(doc)

        self.assertEqual(3, len(doc.mention_chains))
        self.assertEqual(sorted([1, 1, 3]), sorted(list(map(len, doc.mention_chains))))


class AcronymStageTest(unittest.TestCase):
    def test(self):
        doc = unittest.mock.Mock()
        doc.mention_chains = [
            MentionChain([
                Mention('South Carolina', '_DF_doc34', (141, 149), (22, 23), EntityType.GPE, 'Men1'),
                Mention('south carolina', '_DF_doc34', (173, 181), (36, 37), EntityType.GPE, 'Men3')
            ]),
            MentionChain([Mention('SC', '_DF_doc34', (146, 154), (24, 25), EntityType.GPE, 'Men2')]),
            MentionChain([Mention('SC', '_DF_doc34', (146, 154), (24, 25), EntityType.ORG, 'Men6')]),
            MentionChain([
                Mention('ed Smith', '_DF_doc34', (186, 194), (51, 52), EntityType.PER, 'Men4'),
                Mention('Ed Smith', '_DF_doc34', (237, 245), (71, 72), EntityType.PER, 'Men5')
            ]),
        ]
        stage = AcronymStage(2)
        stage.update(doc)
        self.assertEqual(3, len(doc.mention_chains))
        self.assertEqual({1, 2, 3}, {len(x.mentions) for x in doc.mention_chains})

    def test_across_entity_type(self):
        doc = unittest.mock.Mock()
        doc.mention_chains = [
            MentionChain([
                Mention('South Carolina', '_DF_doc34', (141, 149), (22, 23), EntityType.GPE, 'Men1'),
            ]),
            MentionChain([Mention('SC', '_DF_doc34', (146, 154), (24, 25), EntityType.ORG, 'Men6')]),
        ]
        stage = AcronymStage(2)
        stage.update(doc)
        self.assertEqual(2, len(doc.mention_chains))


class PersonLastNameStageTest(unittest.TestCase):
    def test(self):
        doc = unittest.mock.Mock()
        doc.mention_chains = [
            MentionChain([Mention('Ed Smith', '_DF_doc34', (141, 149), (22, 23), EntityType.PER, 'Men1')]),
            MentionChain([Mention('Smith', '_DF_doc34', (146, 154), (24, 25), EntityType.PER, 'Men2')]),
            MentionChain([Mention('Ben Smithy', '_DF_doc34', (173, 181), (36, 37), EntityType.PER, 'Men3')]),
            MentionChain([Mention('ed smith', '_DF_doc34', (186, 194), (51, 52), EntityType.PER, 'Men4')]),
            MentionChain([Mention('Tony Smith', '_DF_doc34', (237, 245), (71, 72), EntityType.ORG, 'Men5')]),
            MentionChain([Mention('Smith Jones', '_DF_doc34', (298, 306), (36, 37), EntityType.PER, 'Men6')]),
        ]
        stage = PersonLastNameStage()
        stage.update(doc)

        self.assertEqual(4, len(doc.mention_chains))
        self.assertEqual(sorted([1, 1, 1, 3]), sorted(list(map(len, doc.mention_chains))))
