import unittest
from hamerkop.core import Document, EntityType, Mention
from hamerkop.coref import *


class UnchainedCoRefTest(unittest.TestCase):
    def test(self):
        doc = Document([
            Mention('Ed Smith', 'doc34', (141, 149), (22, 23), EntityType.PER, 'Men1'),
            Mention('Ed Smith', 'doc34', (146, 154), (24, 25), EntityType.PER, 'Men2'),
            Mention('Ben Smith', 'doc34', (173, 181), (36, 37), EntityType.PER, 'Men3'),
        ], [])
        coref = UnchainedCoRef()
        coref.coref(doc)

        self.assertEqual(3, len(doc.mention_chains))
