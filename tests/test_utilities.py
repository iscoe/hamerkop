import unittest
from hamerkop.core import EntityType, Mention
from hamerkop.utilities import *


class CaseInsensitiveSetTest(unittest.TestCase):
    def test_init(self):
        a = CaseInsensitiveSet(['test', 'Test'])
        self.assertEqual(1, len(a))

    def test_add(self):
        a = CaseInsensitiveSet()
        a.add('Test')
        a.add('test')
        self.assertEqual(1, len(a))

    def test_in(self):
        a = CaseInsensitiveSet()
        a.add('Test')
        self.assertIn('test', a)

    def test_discard(self):
        a = CaseInsensitiveSet(['test'])
        a.discard('Test')
        self.assertEqual(0, len(a))


class IdentifierTest(unittest.TestCase):
    def test_simple(self):
        mention = Mention("Ted", "IL9_SM_001", (4, 8), (0, 1), EntityType.PER)
        ia = InProcessIncremental()
        ia.assign(mention)
        self.assertEqual('M1', mention.id)
        ia.assign(mention)
        self.assertEqual('M2', mention.id)
