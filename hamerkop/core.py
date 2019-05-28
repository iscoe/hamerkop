
class EntityType(object):
    PER = "PER"
    ORG = "ORG"
    GPE = "GPE"
    LOC = "LOC"
    TYPES = [PER, ORG, GPE, LOC]

    @classmethod
    def get(cls, s):
        s = s.upper()
        if s == cls.PER:
            return cls.PER
        if s == cls.ORG:
            return cls.ORG
        if s == cls.GPE:
            return cls.GPE
        if s == cls.LOC:
            return cls.LOC


class EntityContext(object):
    gpe_loc_of_association = 0
    # PER
    title_or_position = 1
    org_of_association = 2
    role_in_incident = 3
    year_of_birth = 4
    year_of_death = 5
    gender = 6
    family_member = 7
    # ORG
    note = 8
    aim = 9
    date_established = 10
    date_established_note = 11
    website = 12
    members_employees_per = 13
    parent_org = 14
    executive_board_members = 15
    jurisdiction = 16
    trusteeship_council = 17
    national_societies = 18

    TABLE = [
        'gpe_loc_of_association',
        'title_or_position',
        'org_of_association',
        'role_in_incident',
        'year_of_birth',
        'year_of_death',
        'gender',
        'family_member',
        'note',
        'aim',
        'date_established',
        'date_established_note',
        'website',
        'members_employees_per',
        'parent_org',
        'executive_board_members',
        'jurisdiction',
        'trusteeship_council',
        'national_societies',
    ]

    @classmethod
    def get_index(cls, key):
        key = key.replace('per:', '')
        key = key.replace('org:', '')
        return cls.TABLE.index(key.strip())

    @classmethod
    def get_value(cls, index):
        return cls.TABLE[index]


class EntityMention(object):
    """
    Entity Mention
    :string id: Unique mention id
    :string string: Mention string (maybe be normalized)
    :string docid: Document id
    :tuple offsets: Offsets into the original document
    :string type: Entity type. See EntityType.
    :string original_string: Original mention string from the document
    """

    def __init__(self, string, docid, offsets, token_offsets, type, id=None):
        # id is often assigned after creation
        self.id = id
        self.string = string
        self.original_string = string
        self.translation = False
        self.docid = docid
        self.offsets = offsets
        self.token_offsets = token_offsets
        self.type = type

    def __repr__(self):
        return "EntityMention({}, {}, {})".format(self.id, self.string, self.type)

class Document(object):
    """
    Document with its tokens and entity mentions
    :list mentions: List of entity mentions
    :list tokens: List of tokens
    :string docid: Doc ID of the original document
    :string lang: 3 letter lang code (see the Lang class). It is a guess from docid.
    """

    def __init__(self, mentions, tokens):
        self.mentions = mentions
        self.tokens = tokens
        self.docid = self.mentions[0].docid