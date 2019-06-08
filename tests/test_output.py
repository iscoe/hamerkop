import io
import os
import unittest
from hamerkop.output import *
from hamerkop.core import Document, Entity, EntityOrigin, EntityType, Mention, MentionChain
from hamerkop.lang import Lang


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class OutputWriterTest(unittest.TestCase):
    def test(self):
        chains = [
            MentionChain([
                Mention('Henry', 'doc34', (123, 128), (17, 17), EntityType.PER, 'Men1')
            ]),
            MentionChain([
                Mention('Ed Smith', 'doc34', (141, 149), (22, 23), EntityType.PER, 'Men2'),
                Mention('Ed', 'doc34', (197, 199), (44, 44), EntityType.PER, 'Men3')
            ])
        ]
        chains[0].entity = Entity('67', EntityType.PER, 'Henry', EntityOrigin.WLL)
        chains[1].entity = None
        doc = Document(chains[0].mentions + chains[1].mentions, [], Lang.EN)
        doc.mention_chains = chains

        buffer = io.StringIO()
        writer = OutputWriter(buffer, 'test', 0.75)
        writer.write(doc)

        buffer.seek(0)
        lines = buffer.readlines()
        line1 = "test\tMen1\tHenry\tdoc34:123-128\t67\tPER\tNAM\t0.75"
        self.assertEqual(line1, lines[0].strip())


class OutputReaderTest(unittest.TestCase):
    def test(self):
        filename = get_filename('data/output/ground_truth.tab')
        with open(filename, 'r') as fp:
            data = OutputReader.read(fp)
        self.assertEqual(4, len(data))

        paris = data['IL9_NW_020583_20180425_I0040RHG9'][(1620, 1624)]
        self.assertEqual(EntityType.GPE, paris.entity_type)
        self.assertEqual(LinkType.LINK, paris.link_type)
        self.assertEqual('2988507', paris.links[0])

        congo = data['IL9_NW_020595_20171201_I0040RCHV'][(180, 184)]
        self.assertEqual(EntityType.GPE, congo.entity_type)
        self.assertEqual(LinkType.LINK, congo.link_type)
        self.assertEqual(3, len(congo.links))
        self.assertEqual('203312', congo.links[0])

        diane = data['IL9_WL_020632_20171020_I0040S56W'][(1633, 1637)]
        self.assertEqual(EntityType.PER, diane.entity_type)
        self.assertEqual(LinkType.NIL, diane.link_type)
