import unittest
from hamerkop.candidates import *
from hamerkop.core import Document, EntityType, Mention, MentionChain


class MockGeneratorTest(unittest.TestCase):
    def test_people(self):
        gen = MockGenerator(5)
        chain = MentionChain([
            Mention('Henry', 'doc34', (0, 1), (0, 1), EntityType.PER),
        ])
        doc = Document(chain.mentions, [])
        doc.mention_chains = [chain]
        gen.find(doc)
        self.assertEqual(5, len(doc.mention_chains[0].candidates))
        self.assertEqual(EntityType.PER, doc.mention_chains[0].candidates[0].type)
