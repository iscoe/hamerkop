import unittest
import unittest.mock
from hamerkop.candidates import *
from hamerkop.core import Entity, EntityOrigin, EntityType, Mention, MentionChain


class MockGenerator(CandidateGenerator):
    def __init__(self, entities):
        self.entities = entities

    def find(self, mention_chain):
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
        candidates = gen.find(chain)
        self.assertEqual(2, len(candidates))


class CachingGeneratorTest(unittest.TestCase):
    def test(self):
        with unittest.mock.patch.multiple(CandidateGenerator, __abstractmethods__=set()):
            mock = CandidateGenerator()
            mock.find = unittest.mock.Mock(side_effect=[
                [Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)],
                [Entity('78', EntityType.PER, 'George', EntityOrigin.WLL)]
            ])
        gen = CachingGenerator(mock)
        chain1 = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain1)
        self.assertEqual('67', candidates[0].id)
        candidates = gen.find(chain1)
        self.assertEqual('67', candidates[0].id)
        mock.find.assert_called_once_with(chain1)
        chain2 = MentionChain([
            Mention('Susan', 'doc35', (0, 1), (0, 1), EntityType.PER, 'Men1'),
        ])
        candidates = gen.find(chain2)
        self.assertEqual('78', candidates[0].id)
