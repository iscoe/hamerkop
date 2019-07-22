import unittest
from hamerkop.core import *


class MentionChainTest(unittest.TestCase):
    def test_name(self):
        mentions = [
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bobby', 'doc1', (0, 1), (0, 1), EntityType.PER),
        ]
        chain = MentionChain(mentions)
        self.assertEqual('Bobby', chain.name)

    def test_get_translit_name(self):
        chain = MentionChain([
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bobby', 'doc1', (0, 1), (0, 1), EntityType.PER),
        ])
        chain.mentions[0].translit_string = 'Robert'
        chain.mentions[1].translit_string = 'Robby'
        self.assertEqual('Robert', chain.get_translit_string())

    def test_get_translit_name_with_nones(self):
        chain = MentionChain([
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bobby', 'doc1', (0, 1), (0, 1), EntityType.PER),
        ])
        self.assertIsNone(chain.get_translit_string())
