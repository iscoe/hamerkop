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

    def test_get(self):
        v = FeatureVector()
        v.add(True)
        v.add(False)
        v.add(17)
        v.add(-1.2)
        x = v.get()
        self.assertEqual(1, x[0])
        self.assertEqual(0, x[1])
        self.assertEqual(17, x[2])
        self.assertAlmostEqual(-1.2, x[3])


class OriginFeatureTest(unittest.TestCase):
    def test1(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.PER, 'Christopher', EntityOrigin.WLL)
        OriginFeature().extract(None, entity, None, v)
        self.assertEqual(0, v.data[0])

    def test2(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.PER, 'Christopher', EntityOrigin.AUG)
        OriginFeature().extract(None, entity, None, v)
        self.assertEqual(1, v.data[0])


class WikipediaFeatureTest(unittest.TestCase):
    def test_positive(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York', EntityOrigin.GEO, urls=['http://en.wikipedia.org/wiki/New_York_City'])
        entity.names = {'New York', 'New York City', 'NYC'}
        chain = MentionChain([Mention('New York City', 'doc1', (), (), EntityType.GPE)])
        WikipediaFeature().extract(chain, entity, None, v)
        self.assertTrue(v.data[0])

    def test_negative(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York', EntityOrigin.GEO, urls=['http://en.wikipedia.org/wiki/New_York'])
        chain = MentionChain([Mention('New York City', 'doc1', (), (), EntityType.GPE)])
        WikipediaFeature().extract(chain, entity, None, v)
        self.assertFalse(v.data[0])


class ExactMatchFeatureTest(unittest.TestCase):
    def test_match(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York', EntityOrigin.GEO)
        entity.names = {'New York', 'New York City', 'NYC'}
        chain = MentionChain([Mention('Nueva York', 'doc1', (), (), EntityType.GPE)])
        chain.mentions[0].translate_string = 'new york'
        ExactMatchFeature().extract(chain, entity, None, v)
        self.assertTrue(v.data[0])

    def test_no_match(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'Nueva York', EntityOrigin.GEO)
        chain = MentionChain([Mention('New York', 'doc1', (), (), EntityType.GPE)])
        ExactMatchFeature().extract(chain, entity, None, v)
        self.assertFalse(v.data[0])


class SharedTokensFeatureTest(unittest.TestCase):
    def test(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York City', EntityOrigin.GEO)
        entity.names = {'NYC', 'New York'}
        chain = MentionChain([Mention('Nueva York', 'doc1', (), (), EntityType.GPE)])
        SharedTokensFeature().extract(chain, entity, None, v)
        self.assertAlmostEqual(0.5, v.data[0])


class LastNameFeatureTest(unittest.TestCase):
    def test_positive(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.PER, 'John Smith', EntityOrigin.WLL)
        chain = MentionChain([Mention('Jep Smith', 'doc1', (), (), EntityType.PER)])
        LastNameFeature().extract(chain, entity, None, v)
        self.assertTrue(v.data[0])

    def test_negative(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.PER, 'John Smith', EntityOrigin.WLL)
        chain = MentionChain([Mention('Jep Miller', 'doc1', (), (), EntityType.PER)])
        LastNameFeature().extract(chain, entity, None, v)
        self.assertFalse(v.data[0])

    def test_not_multi_token_name(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.PER, 'John Smith', EntityOrigin.WLL)
        chain = MentionChain([Mention('Smith', 'doc1', (), (), EntityType.PER)])
        LastNameFeature().extract(chain, entity, None, v)
        self.assertFalse(v.data[0])


class LevenshteinFeatureTest(unittest.TestCase):
    def test(self):
        v = FeatureVector()
        entity = Entity('1', EntityType.GPE, 'New York City', EntityOrigin.GEO)
        entity.names = {'NYC', 'New York'}
        chain = MentionChain([Mention('Nueva York', 'doc1', (), (), EntityType.GPE)])
        LevenshteinFeature().extract(chain, entity, None, v)
        self.assertAlmostEqual(3/10, v.data[0])
