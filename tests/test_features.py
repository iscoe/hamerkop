import unittest
from hamerkop.features import *
from hamerkop.core import Entity, EntityOrigin, EntityType, Mention, MentionChain


class FeatureVectorTest(unittest.TestCase):
    def test_add_single_value(self):
        v = FeatureVector()
        v.add(36)
        self.assertEqual(36, v.data[0])

    def test_add_list(self):
        v = FeatureVector()
        v.add([1, 3])
        self.assertEqual([1, 3], v.data)

    def test_add_var_types(self):
        v = FeatureVector()
        v.add(True)
        v.add(97)
        self.assertEqual([True, 97], v.data)


class ExactMatchExtractorTest(unittest.TestCase):
    def test_match(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York', EntityOrigin.GEO)
        entity.names = {'New York', 'New York City', 'NYC'}
        chain = MentionChain([Mention('Nueva York', 'doc1', (), (), EntityType.GPE)])
        chain.mentions[0].translate_string = 'new york'
        ExactMatchExtractor().extract(chain, entity, None, v)
        self.assertTrue(v.data[0])

    def test_no_match(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'Nueva York', EntityOrigin.GEO)
        chain = MentionChain([Mention('New York', 'doc1', (), (), EntityType.GPE)])
        ExactMatchExtractor().extract(chain, entity, None, v)
        self.assertFalse(v.data[0])
