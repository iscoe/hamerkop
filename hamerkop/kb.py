from abc import ABC, abstractmethod


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
