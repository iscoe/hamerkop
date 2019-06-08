from abc import ABC, abstractmethod
import collections
import csv
import logging
import os

from .core import Entity, EntityType
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)

"""LoReHLT Knowledge Base columns"""
KBColumns = [
    'origin',
    'entity_type',
    'entityid',
    'name',
    'asciiname',
    'latitude',
    'longitude',
    'feature_class',
    'feature_class_name',
    'feature_code',
    'feature_code_name',
    'feature_code_description',
    'country_code',
    'country_code_name',
    'cc2',
    'admin1_code',
    'admin1_code_name',
    'admin2_code',
    'admin2_code_name',
    'admin3_code',
    'admin4_code',
    'population',
    'elevation',
    'dem',
    'timezone',
    'modification_date',
    'per_gpe_loc_of_association',
    'per_title_or_position',
    'per_org_of_association',
    'per_role_in_incident',
    'per_year_of_birth',
    'per_year_of_death',
    'per_gender',
    'per_family_member',
    'note',
    'aim',
    'org_date_established',
    'date_established_note',
    'org_website',
    'org_gpe_loc_of_association',
    'org_members_employees_per',
    'org_parent_org',
    'executive_board_members',
    'jurisdiction',
    'trusteeship_council',
    'national_societies',
    'external_link'
]


class KBException(Exception):
    """An error occurred when interacting with the KB."""


class KB(ABC):
    """
    Knowledge base interface
    Provides methods for retrieving entities but not searching for them.
    See NameIndex for search methods.
    """

    @abstractmethod
    def size(self):
        """
        Get the number of entities in the KB
        :return: int
        """
        pass

    @abstractmethod
    def get_entity(self, entity_id):
        """
        Get an entity
        :param entity_id: string
        :return: Entity
        """
        pass

    @abstractmethod
    def get_entities(self, entity_ids):
        """
        Get a list of entities
        :param entity_ids: list of entity ids
        :return: list
        """
        pass


class NameIndex(ABC):
    """
    Find candidates based on a name string
    """
    @abstractmethod
    def find(self, name, type, limit=25):
        """
        Find entities that possibly match this name and type pair
        :param name: name string
        :param type: EntityType string
        :param limit: maximum number of candidates to return
        :return: list of Entity objects
        """
        pass


class MemoryKB(KB):
    """
    KB backed by a python dictionary for smaller kbs
    """
    def __init__(self, entities_filename, alt_names_filename):
        """
        :param entities_filename: filename for the entities file
        :param alt_names_filename: filename for the alternate names file
        """
        for filename in [entities_filename, alt_names_filename]:
            if not os.path.exists(filename):
                raise KBException("{} does not exist".format(filename))

        self.entities = self._read_entities(entities_filename)
        self._add_alt_names(self.entities, alt_names_filename)

    def size(self):
        return len(self.entities)

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def get_entities(self, entity_ids):
        return [self.entities[x] for x in entity_ids if x in self.entities]

    def __iter__(self):
        for entity in self.entities.values():
            yield entity

    def _generate_entities(self, entity_rows, name_rows):
        entities = collections.OrderedDict()
        for row in entity_rows:
            if row['entityid'] not in entities:
                entity = Entity(row['entityid'], row['entity_type'], row['name'], row['origin'],
                                None, str(row['latitude']), str(row['longitude']),
                                row['country_code'], row['population'], row['external_link'])
                entities[entity.id] = entity
        for row in name_rows:
            entities[row['entityid']].names.add(row['alternatename'])
        return list(entities.values())

    def _read_entities(self, filename):
        entities = {}
        with open(filename, 'r') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            next(reader)
            for row in reader:
                entity = self._generate_entity(row)
                entities[entity.id] = entity
        return entities

    def _add_alt_names(self, entities, filename):
        with open(filename, 'r') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            next(reader)
            for row in reader:
                entity_id = row[0]
                alt_name = row[1]
                entities[entity_id].names.add(alt_name)

    @staticmethod
    def _generate_entity(row):
        return Entity(row[2], row[1], row[3], row[0], None, row[5], row[6], row[12], row[21])


class ExactMatchMemoryNameIndex(NameIndex):
    """
    Builds an in memory index
    """
    def __init__(self, kb):
        self.kb = kb
        self.index = self._build_index()

    def find(self, name, type, limit=25):
        if name in self.index[type]:
            return self.kb.get_entities(self.index[type][name])
        else:
            return []

    def _build_index(self):
        index = {}
        for entity_type in EntityType.TYPES:
            index[entity_type] = CaseInsensitiveDict()
        for entity in self.kb:
            for name in entity.names:
                if name not in index[entity.type]:
                    index[entity.type][name] = []
                index[entity.type][name].append(entity.id)
        return index
