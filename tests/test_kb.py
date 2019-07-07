import unittest
import os
from hamerkop.kb import *
from hamerkop.core import EntityOrigin, EntityType


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class EntityCreatorTest(unittest.TestCase):
    def test(self):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        with open(entities_filename, 'r') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            next(reader)
            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertEqual('1', entity.id)
            self.assertEqual(EntityType.GPE, entity.type)
            self.assertEqual(EntityOrigin.GEO, entity.origin)
            self.assertEqual('New York City', entity.name)
            self.assertIsInstance(entity.context, GeoContext)
            self.assertAlmostEqual(42.6499, entity.context.latitude)
            self.assertAlmostEqual(11.53335, entity.context.longitude)
            self.assertEqual('US', entity.context.country)
            self.assertEqual(999, entity.context.population)
            self.assertEqual(2, len(entity.urls))

            row = next(reader)
            entity = EntityCreator.create(row)
            self.assertEqual('2', entity.id)
            self.assertEqual(0, len(entity.urls))
            self.assertIsNone(entity.context)

            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertIsInstance(entity.context, PerContext)
            self.assertEqual('Boston', entity.context.location)
            self.assertEqual(['President', 'Vice President'], entity.context.titles)
            self.assertEqual(['USA'], entity.context.organizations)

            row = next(reader)
            entity = EntityCreator.create(row)
            self.assertEqual('11', entity.id)

            row = next(reader)
            entity = EntityCreator.create(row, include_context=True)
            self.assertEqual('17', entity.id)
            self.assertEqual(EntityType.ORG, entity.type)
            self.assertEqual(EntityOrigin.APB, entity.origin)
            self.assertEqual('UNICEF', entity.name)
            self.assertIsInstance(entity.context, OrgContext)
            self.assertEqual('New York City', entity.context.location)


class MemoryKBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        with open(entities_filename, 'r') as entities_fp, open(alt_names_filename, 'r') as names_fp:
            cls.kb = MemoryKB(entities_fp, names_fp, cache=False)

    def test_getting_person(self):
        entity = self.kb.get_entity('10')
        self.assertEqual('10', entity.id)
        self.assertIn('JDawg', entity.names)

    def test_getting_person_not_in_kb(self):
        entity = self.kb.get_entity('13')
        self.assertIsNone(entity)

    def test_getting_multiple_entities(self):
        entities = self.kb.get_entities(['1', '5', '11'])
        self.assertEqual(2, len(entities))

    def test_iterator(self):
        entity_ids = [entity.id for entity in self.kb]
        self.assertEqual(5, len(entity_ids))
        self.assertIn('10', entity_ids)


class ExactMatchMemoryNameIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        with open(entities_filename, 'r') as entities_fp, open(alt_names_filename, 'r') as names_fp:
            cls.kb = MemoryKB(entities_fp, names_fp, cache=False)

    def test(self):
        index = ExactMatchMemoryNameIndex(self.kb)
        entities = index.find('John', EntityType.PER)
        self.assertEqual(2, len(entities))


class NgramMemoryNameIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        with open(entities_filename, 'r') as entities_fp, open(alt_names_filename, 'r') as names_fp:
            cls.kb = MemoryKB(entities_fp, names_fp, cache=False)

    def test_build_index(self):
        index = NgramMemoryNameIndex(self.kb, 4)
        self.assertTrue(('1', 0), index.index[EntityType.GPE]['_new'])
