import unittest
import unittest.mock
from hamerkop.candidates import *
from hamerkop.core import Entity, EntityOrigin, EntityType, Link, LinkType, Mention, MentionChain


class CandidatesScorerTest(unittest.TestCase):
    def test(self):
        gt = {'doc1': {
            (0, 2): Link(EntityType.PER, LinkType.LINK, ['123', '122'], None),
            (4, 8): Link(EntityType.PER, LinkType.NIL, [], 'NIL999'),
            (10, 12): Link(EntityType.PER, LinkType.LINK, ['222'], None),
            (16, 17): Link(EntityType.PER, LinkType.LINK, ['333'], None),
        }}
        doc = unittest.mock.Mock()
        doc.doc_id = 'doc1'
        doc.mention_chains = [
            MentionChain([
                Mention('', 'doc1', (0, 2), (), EntityType.PER),
                Mention('', 'doc1', (3, 7), (), EntityType.PER),
                Mention('', 'doc1', (16, 17), (), EntityType.PER),
            ]),
            MentionChain([Mention('', 'doc1', (4, 8), (), EntityType.PER)]),
            MentionChain([Mention('', 'doc1', (10, 12), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [Entity('122', EntityType.PER, '', EntityOrigin.WLL)]
        doc.mention_chains[1].candidates = [Entity('147', EntityType.PER, '', EntityOrigin.WLL)]
        doc.mention_chains[2].candidates = [
            Entity('198', EntityType.PER, '', EntityOrigin.WLL),
            Entity('222', EntityType.PER, '', EntityOrigin.WLL),
        ]
        scorer = CandidatesScorer(gt)
        scorer.update(doc)
        self.assertEqual(3, scorer.report.num_mentions_with_links[EntityType.PER])
        self.assertEqual(2, scorer.report.num_including_correct_entity[EntityType.PER])


class MockGenerator(CandidateGenerator):
    def __init__(self, entities):
        self.entities = entities

    def find(self, mention_chain, document):
        return self.entities


class CombiningGeneratorTest(unittest.TestCase):
    def test(self):
        mock1 = MockGenerator([
            Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)
        ])
        mock2 = MockGenerator([
            Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL),
            Entity('73', EntityType.PER, 'Henri', EntityOrigin.WLL)
        ])
        gen = CombiningGenerator([mock1, mock2])
        chain = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain, unittest.mock.Mock())
        self.assertEqual(2, len(candidates))


class CascadeGeneratorTest(unittest.TestCase):
    def test(self):
        mock1 = MockGenerator([
            Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)
        ])
        mock2 = MockGenerator([
            Entity('61', EntityType.PER, 'Henry', EntityOrigin.WLL),
            Entity('73', EntityType.PER, 'Henri', EntityOrigin.WLL)
        ])
        mock3 = MockGenerator([
            Entity('99', EntityType.PER, 'Henry', EntityOrigin.WLL)
        ])
        gen = CascadeGenerator([mock1, mock2, mock3], 2)
        chain = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain, unittest.mock.Mock())
        self.assertEqual(3, len(candidates))


class CachingGeneratorTest(unittest.TestCase):
    def test(self):
        with unittest.mock.patch.multiple(CandidateGenerator, __abstractmethods__=set()):
            mock = CandidateGenerator()
            mock.find = unittest.mock.Mock(side_effect=[
                [Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)],
                [Entity('78', EntityType.PER, 'George', EntityOrigin.WLL)]
            ])
        gen = CachingGenerator(mock)
        doc = unittest.mock.Mock()
        chain1 = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain1, doc)
        self.assertEqual('67', candidates[0].id)
        candidates = gen.find(chain1, doc)
        self.assertEqual('67', candidates[0].id)
        mock.find.assert_called_once_with(chain1, doc)
        chain2 = MentionChain([
            Mention('Susan', 'doc35', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain2, doc)
        self.assertEqual('78', candidates[0].id)
