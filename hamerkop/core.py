import collections


class EntityType:
    """LoReHLT entity types"""
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


class EntityOrigin:
    GEO = "geonames"
    WLL = "cia word leaders"
    APB = "cia word fact book orgs"
    AUG = "augmentation"


class EntityContext:
    """LoReHLT KB entity features"""
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


class Entity:
    """
    Entity from a Knowledge Base
    :string id: Entity ID
    :string type: Entity type
    :string name: Canonical name from the KB
    :set names: All names for entity from the KB
    :string type: EntityType
    :string origin: Origin of the entity
    :string latitude: Latitude of entity for most GPE and LOC
    :string longitude: Longitude of entity for most GPE and LOC
    :string country: ISO-3166 2-letter country code for GPE and LOC
    :int population: Population count for some GPE and LOC
    :dict context: Other fields like title, role, family members, etc.
    :list urls: All websites for this entity
    """

    def __init__(self, id, type, name, origin, context=None, lat=None, lon=None, country=None, pop=None, urls=None):
        self.id = id
        self.type = type
        self.name = name
        self.names = {name}
        self.source = origin
        self.context = context if context else {}
        self.latitude = lat
        self.longitude = lon
        self.country = country
        self.population = int(pop) if pop else 0
        self.urls = urls.split('|') if urls else []

    def __repr__(self):
        return "Entity({}, {}, {})".format(self.id, self.name, self.type)

    def __str__(self):
        return "{}\t{}\t{}\t{}\t{}".format(self.id, self.name, self.type, self.country, ','.join(self.names))


class Mention:
    """
    Entity Mention
    :string id: Unique mention id
    :string string: Mention string (maybe be normalized)
    :string docid: Document id
    :tuple offsets: Character offsets into the original document
    :tuple token_offsets: Token offsets into the original document
    :string type: Entity type. See EntityType.
    :string original_string: Original mention string from the document
    :string native_string: Set if string is translated or transliterated
    """

    def __init__(self, string, docid, offsets, token_offsets, type, id=None):
        # id is often assigned after creation
        self.id = id
        self.string = string
        self.original_string = string
        self.native_string = None
        self.docid = docid
        self.offsets = offsets
        self.token_offsets = token_offsets
        self.type = type

    def __repr__(self):
        return "Mention({}, {}, {})".format(self.id, self.string, self.type)


class MentionChain:
    """
    A chain of mentions from a document
    :list mentions: The list of mentions for this chain
    :list candidates: The list of candidate entities for this chain
    :Entity entity: KB entity that is best match or None
    """

    def __init__(self, mentions):
        self.mentions = mentions
        self.candidates = None
        self.entity = None
        self._name = None

    @property
    def name(self):
        """Best name string for mention chain"""
        if self._name is None:
            # longest name string is default
            self._name = max([x.string for x in self.mentions], key=len)
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        return self.mentions[0].type

    def __len__(self):
        return len(self.mentions)

    def __repr__(self):
        return "MentionChain for {}: {} mentions".format(self.name, len(self.mentions))


class Document:
    """
    Document with its tokens and entity mentions
    :list mentions: List of entity mentions
    :list tokens: List of tokens
    :string docid: Doc ID of the original document
    :list mention_chains: List of MentionChain objects
    """

    def __init__(self, mentions, tokens, lang):
        self.mentions = mentions
        self.tokens = tokens
        self.lang = lang
        self.docid = self.mentions[0].docid
        self.mention_chains = None

    def __repr__(self):
        return "Document({}) with {} mentions".format(self.docid, len(self.mentions))


class Pipeline:
    """
    Entity linking pipeline
    """

    def __init__(self, documents, preprocessor, coref, candidate_gen, resolver, writer):
        """
        :param documents: Iterator that produces Document objects
        :param preprocessor: Mention preprocessor
        :param coref: Coreference component
        :param candidate_gen: Candidate generator
        :param resolver: Entity resolution component
        :param writer: Output writer
        """
        self.documents = documents
        self.preprocessor = preprocessor
        self.coref = coref
        self.candidate_gen = candidate_gen
        self.resolver = resolver
        self.writer = writer

    def run(self):
        for doc in self.documents:
            self.preprocessor.process(doc)
            self.coref.coref(doc)
            self.candidate_gen.process(doc)
            self.resolver.resolve(doc)
            self.writer.write(doc)
