import unittest
import unittest.mock
from hamerkop.resolver import *
from hamerkop.core import Entity, EntityOrigin, EntityType, Mention, MentionChain
from hamerkop.io import Link, LinkType


class ResolverScorerTest(unittest.TestCase):
    def test(self):
        gt = {'doc1': {
            (0, 2): Link(EntityType.PER, LinkType.LINK, ['123', '122'], None),
            (4, 8): Link(EntityType.PER, LinkType.NIL, [], 'NIL999'),
            (10, 12): Link(EntityType.PER, LinkType.LINK, ['222'], None),
            (16, 17): Link(EntityType.PER, LinkType.LINK, ['333'], None),
            (18, 19): Link(EntityType.PER, LinkType.LINK, ['444'], None),
        }}
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([
                Mention('', 'doc1', (0, 2), (), EntityType.PER),
                Mention('', 'doc1', (3, 7), (), EntityType.PER),
                Mention('', 'doc1', (16, 17), (), EntityType.PER),
            ]),
            MentionChain([Mention('', 'doc1', (4, 8), (), EntityType.PER)]),
            MentionChain([Mention('', 'doc1', (10, 12), (), EntityType.PER)]),
            MentionChain([Mention('', 'doc1', (18, 19), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [Entity('122', EntityType.PER, '', EntityOrigin.WLL)]
        doc.mention_chains[0].entity = doc.mention_chains[0].candidates[0]
        doc.mention_chains[1].candidates = [Entity('147', EntityType.PER, '', EntityOrigin.WLL)]
        doc.mention_chains[1].entity = doc.mention_chains[1].candidates[0]
        doc.mention_chains[2].candidates = [
            Entity('198', EntityType.PER, '', EntityOrigin.WLL),
            Entity('222', EntityType.PER, '', EntityOrigin.WLL),
        ]
        doc.mention_chains[2].entity = None
        doc.mention_chains[3].candidates = [Entity('17', EntityType.PER, '', EntityOrigin.WLL)]
        doc.mention_chains[3].entity = doc.mention_chains[3].candidates[0]
        scorer = ResolverScorer(gt)
        scorer.update(doc)
        self.assertEqual(2, scorer.report.num_mentions_with_correct_candidate)
        self.assertEqual(1, scorer.report.num_mentions_correct_entity)
