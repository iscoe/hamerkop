import unittest
from hamerkop.core import *


class MentionChainTest(unittest.TestCase):
    def test_best_name(self):
        mentions = [
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bob', 'doc1', (0, 1), (0, 1), EntityType.PER),
            Mention('Bobby', 'doc1', (0, 1), (0, 1), EntityType.PER),
        ]
        chain = MentionChain(mentions)
        self.assertEqual('Bob', chain.best_name)

    def test_best_name_no_mentions(self):
        chain = MentionChain([])
        self.assertIsNone(chain.best_name)
