import unittest
from hamerkop.candidates import *
from hamerkop.core import Document, EntityType, Mention, MentionChain


class MockGeneratorTest(unittest.TestCase):
    def test_people(self):
        gen = MockGenerator(5)
        chain = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER),
        ])
        candidates = gen.find(chain)
        self.assertEqual(5, len(candidates))
        self.assertEqual(EntityType.PER, candidates[0].type)
