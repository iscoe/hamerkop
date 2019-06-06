import unittest
import os
from hamerkop.kb import *


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class MemoryKBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        cls.kb = MemoryKB(entities_filename, alt_names_filename)

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
        self.assertEqual(4, len(entity_ids))
        self.assertIn('10', entity_ids)


class ExactMatchMemoryNameSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        cls.kb = MemoryKB(entities_filename, alt_names_filename)

    def test(self):
        index = ExactMatchMemoryNameSearch(self.kb)
        entities = index.find('John', EntityType.PER)
        self.assertEqual(2, len(entities))
