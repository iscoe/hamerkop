import abc
import csv
import logging

from .core import Entity, EntityType
from .utilities import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class KBException(Exception):
    """An error occurred when interacting with the KB."""


class KB(abc.ABC):
    """
    Knowledge base interface
    Provides methods for retrieving entities but not searching for them.
    See NameIndex for search methods.
    """

    @abc.abstractmethod
    def size(self):
        """
        Get the number of entities in the KB
        :return: int
        """
        pass

    @abc.abstractmethod
    def get_entity(self, entity_id):
        """
        Get an entity
        :param entity_id: string
        :return: Entity
        """
        pass

    @abc.abstractmethod
    def get_entities(self, entity_ids):
        """
        Get a list of entities
        :param entity_ids: list of entity ids
        :return: list
        """
        pass


class EntityCreator:
    """
    Generates an Entity from a row from CSV file
    """
    # LoReHLT Knowledge Base columns
    ORIGIN = 0
    ENTITY_TYPE = 1
    ENTITY_ID = 2
    NAME = 3
    ASCIINAME = 4
    LATITUDE = 5
    LONGITUDE = 6
    FEATURE_CLASS = 7
    FEATURE_CLASS_NAME = 8
    FEATURE_CODE = 9
    FEATURE_CODE_NAME = 10
    FEATURE_CODE_DESCRIPTION = 11
    COUNTRY_CODE = 12
    COUNTRY_CODE_NAME = 13
    CC2 = 14
    ADMIN1_CODE = 15
    ADMIN1_CODE_NAME = 16
    ADMIN2_CODE = 17
    ADMIN2_CODE_NAME = 18
    ADMIN3_CODE = 19
    ADMIN4_CODE = 20
    POPULATION = 21
    ELEVATION = 22
    DEM = 23
    TIMEZONE = 24
    MODIFICATION_DATE = 25
    PER_GPE_LOC_OF_ASSOCIATION = 26
    PER_TITLE_OR_POSITION = 27
    PER_ORG_OF_ASSOCIATION = 28
    PER_ROLE_IN_INCIDENT = 29
    PER_YEAR_OF_BIRTH = 30
    PER_YEAR_OF_DEATH = 31
    PER_GENDER = 32
    PER_FAMILY_MEMBER = 33
    NOTE = 34
    AIM = 35
    ORG_DATE_ESTABLISHED = 36
    DATE_ESTABLISHED_NOTE = 37
    ORG_WEBSITE = 38
    ORG_GPE_LOC_OF_ASSOCIATION = 39
    ORG_MEMBERS_EMPLOYEES_PER = 40
    ORG_PARENT_ORG = 41
    EXECUTIVE_BOARD_MEMBERS = 42
    JURISDICTION = 43
    TRUSTEESHIP_COUNCIL = 44
    NATIONAL_SOCIETIES = 45
    EXTERNAL_LINK = 46

    @classmethod
    def create(cls, row, include_context=False):
        # TODO: not processing context yet
        keys = [cls.ENTITY_ID, cls.ENTITY_TYPE, cls.NAME, cls.ORIGIN, cls.LATITUDE,
                cls.LONGITUDE, cls.COUNTRY_CODE, cls.POPULATION, cls.EXTERNAL_LINK]
        data = [row[key] for key in keys]
        data[-1] = [] if data[-1] == '' else data[-1].split('|')
        data[4] = cls._float(data[4])
        data[5] = cls._float(data[5])
        data[6] = data[6] if data[6] else None
        data[7] = cls._int(data[7])
        entity = Entity(*data)
        return entity

    @staticmethod
    def _float(value):
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _int(value):
        try:
            return int(value)
        except ValueError:
            return None


class MemoryKB(KB):
    """
    KB backed by a python dictionary for smaller kbs.

    The dictionary is entity ID -> Entity object
    """
    def __init__(self, entities_fp, alt_names_fp, verbose=False):
        """
        :param entities_fp: handle for reading the entities file
        :param alt_names_fp: handle for reading the alternate names file
        :param verbose: Whether to write entity loading progress to STDOUT
        """
        self.verbose = verbose
        self.entities = self._load_entities(entities_fp)
        self._load_alt_names(alt_names_fp)

    def size(self):
        return len(self.entities)

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    def get_entities(self, entity_ids):
        return [self.entities[x] for x in entity_ids if x in self.entities]

    def __iter__(self):
        for entity in self.entities.values():
            yield entity

    def _load_entities(self, fp):
        entity_count = 0
        entities = {}
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            entity = EntityCreator.create(row)
            entities[entity.id] = entity
            entity_count += 1
            if self.verbose and entity_count % 1000 == 0:
                print('KB loading: {0: >10,}'.format(entity_count), end='\r')
        logger.info('Loaded {} entities'.format(len(entities)))
        if self.verbose:
            # clear the progress text by writing long blank string
            print(' ' * 40, end='\r')
        return entities

    def _load_alt_names(self, fp):
        name_count = 0
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            entity_id = row[0]
            alt_name = row[1]
            if entity_id in self.entities:
                name_count += 1
                self.entities[entity_id].names.add(alt_name)
        logger.info('Loaded {} alternate names'.format(name_count))


class NameIndex(abc.ABC):
    """
    Find candidates based on a name string
    """
    @abc.abstractmethod
    def find(self, name, type, limit=25):
        """
        Find entities that possibly match this name and type pair
        :param name: name string
        :param type: EntityType string
        :param limit: maximum number of candidates to return
        :return: list of Entity objects
        """
        pass


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
