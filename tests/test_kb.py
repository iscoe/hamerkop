import unittest
import unittest.mock
import os
from hamerkop.kb import *
from hamerkop.core import EntityType
from hamerkop.io import EntityLoader


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class MemoryKBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities_filename = get_filename('data/kb/small_kb_entities.tab')
        alt_names_filename = get_filename('data/kb/small_kb_alternate_names.tab')
        with open(entities_filename, 'r') as entities_fp, open(alt_names_filename, 'r') as names_fp:
            loader = EntityLoader(entities_fp, names_fp)
            cls.kb = MemoryKB(loader)

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
            loader = EntityLoader(entities_fp, names_fp)
            cls.kb = MemoryKB(loader)

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
            loader = EntityLoader(entities_fp, names_fp)
            cls.kb = MemoryKB(loader)

    def test_build_index(self):
        index = NgramMemoryNameIndex(self.kb, 4)
        self.assertTrue(('1', 0), index.index[EntityType.GPE]['_new'])


class TypeIgnoringIndexTest(unittest.TestCase):
    def test(self):
        index1 = unittest.mock.Mock()
        index1.find = unittest.mock.Mock()
        index2 = TypeIgnoringIndex(index1, {EntityType.GPE, EntityType.LOC})
        with unittest.mock.patch.object(index1, 'find') as mock:
            index2.find('test', EntityType.GPE, 1)
            self.assertEqual(mock.call_count, 2)
            mock.assert_any_call('test', EntityType.GPE, 1)
            mock.assert_any_call('test', EntityType.LOC, 1)

            mock.reset_mock()
            index2.find('test', EntityType.PER, 1)
            mock.assert_called_once_with('test', EntityType.PER, 1)
