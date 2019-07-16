import unittest
import unittest.mock
from hamerkop.resolver import *
from hamerkop.core import Entity, EntityOrigin, EntityType, Link, LinkType, Mention, MentionChain


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
        self.assertEqual(2, scorer.report.num_mentions_with_correct_candidate[EntityType.PER])
        self.assertEqual(1, scorer.report.num_mentions_correct_entity[EntityType.PER])


class CascadeResolverTest(unittest.TestCase):
    def test(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [
            Entity('122', EntityType.PER, 'John Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_Smith']),
            Entity('123', EntityType.PER, 'John Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_H_Smith']),
            Entity('124', EntityType.PER, 'Jake Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_Smith']),
        ]
        CascadeResolver([ExactNameResolver(), WikipediaResolver()]).resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(2, len(doc.mention_chains[0].candidates))
        self.assertEqual('122', doc.mention_chains[0].entity.id)


class ExactNameResolverTest(unittest.TestCase):
    def test_no_matches(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [Entity('122', EntityType.PER, 'John', EntityOrigin.WLL)]
        ExactNameResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(1, len(doc.mention_chains[0].candidates))
        self.assertIsNone(doc.mention_chains[0].entity)

    def test_one_match(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        entity1 = Entity('122', EntityType.PER, 'John', EntityOrigin.WLL)
        entity1.names = {'John', 'J. Smith', 'john smith'}
        doc.mention_chains[0].candidates = [entity1, Entity('123', EntityType.PER, 'Not John', EntityOrigin.WLL)]
        ExactNameResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(2, len(doc.mention_chains[0].candidates))
        self.assertEqual(entity1, doc.mention_chains[0].entity)

    def test_multiple_matches(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [
            Entity('122', EntityType.PER, 'John Smith', EntityOrigin.WLL),
            Entity('123', EntityType.PER, 'John Smith', EntityOrigin.WLL),
            Entity('124', EntityType.PER, 'Jake Smith', EntityOrigin.WLL),
        ]
        ExactNameResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(2, len(doc.mention_chains[0].candidates))
        self.assertIsNone(doc.mention_chains[0].entity)


class WikipediaResolverTest(unittest.TestCase):
    def test_no_match(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [Entity('122', EntityType.PER, 'John', EntityOrigin.WLL)]
        WikipediaResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(1, len(doc.mention_chains[0].candidates))
        self.assertIsNone(doc.mention_chains[0].entity)

    def test_one_match(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        entity1 = Entity('122', EntityType.PER, 'John', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_Smith'])
        doc.mention_chains[0].candidates = [entity1, Entity('123', EntityType.PER, 'Not John', EntityOrigin.WLL)]
        WikipediaResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(2, len(doc.mention_chains[0].candidates))
        self.assertEqual(entity1, doc.mention_chains[0].entity)

    def test_multiple_matches(self):
        doc = unittest.mock.Mock()
        doc.docid = 'doc1'
        doc.mention_chains = [
            MentionChain([Mention('John Smith', 'doc1', (4, 8), (), EntityType.PER)]),
        ]
        doc.mention_chains[0].candidates = [
            Entity('122', EntityType.PER, 'John Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_Smith']),
            Entity('123', EntityType.PER, 'John Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_Smith']),
            Entity('124', EntityType.PER, 'Jake Smith', EntityOrigin.WLL, urls=['http://en.wikipedia.org/wiki/John_P_Smith']),
        ]
        WikipediaResolver().resolve(doc)
        self.assertEqual(1, len(doc.mention_chains))
        self.assertEqual(2, len(doc.mention_chains[0].candidates))
        self.assertIsNone(doc.mention_chains[0].entity)
