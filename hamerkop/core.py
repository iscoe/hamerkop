# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.


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
    WLL = "cia world leaders"
    APB = "cia world orgs"
    AUG = "augmentation"
    ORIGINS = {GEO, WLL, APB, AUG}

    @classmethod
    def create(cls, string):
        if string in cls.ORIGINS:
            return string
        if string == 'GEO':
            return cls.GEO
        elif string == 'WLL':
            return cls.WLL
        elif string == 'APB':
            return cls.APB
        elif string[:3] == 'AUG':
            return cls.AUG
        else:
            raise ValueError('Unknown origin: {}'.format(string))


class DocType:
    SN = 'twitter'
    WL = 'blog'
    RF = 'reference'
    DF = 'discussion forum'
    NW = 'newswire'

    @classmethod
    def detect(cls, doc_id):
        if '_SN_' in doc_id:
            return cls.SN
        elif '_WL_' in doc_id:
            return cls.WL
        elif '_RF_' in doc_id:
            return cls.RF
        elif '_DF_' in doc_id:
            return cls.DF
        elif '_NW_' in doc_id:
            return cls.NW
        else:
            raise ValueError("Unknown document type for doc id: {}".format(doc_id))


class EntityContext:
    pass


class PerContext(EntityContext):
    def __init__(self, location, titles, organizations):
        """
        :string location: location of the person (usually a country name)
        """
        self.location = location
        self.titles = titles
        self.organizations = organizations

    def __repr__(self):
        return "PerContext({}, {}, {})".format(
            self.location, ','.join(self.titles), ','.join(self.organizations))


class OrgContext(EntityContext):
    def __init__(self, location):
        """
        :string location: location of the organization (usually a country name)
        """
        self.location = location

    def __repr__(self):
        return "OrgContext({})".format(self.location)


class GeoContext(EntityContext):
    def __init__(self, type, country, latitude, longitude, population):
        """
        :string type: type of location (city, lake, road, etc.)
        :string country: name of country
        :float latitude: Latitude of entity for most GPE and LOC
        :float longitude: Longitude of entity for most GPE and LOC
        :string country: ISO-3166 2-letter country code for GPE and LOC
        :int population: Population count for some GPE and LOC
        """
        self.type = type
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
        self.population = population

    def __repr__(self):
        return "GeoContext({}, {}, {}, {}, {})".format(
            self.type, self.country, self.latitude, self.longitude, self.population)


class Entity:
    """
    Entity from a Knowledge Base
    :string id: Entity ID
    :string type: Entity type
    :string name: Canonical name from the KB
    :set names: All names for entity from the KB
    :string origin: Origin of the entity
    :list urls: All websites for this entity
    :EntityContext context: Other fields like location, title, latitude, longitude, etc.
    """
    def __init__(self, id, type, name, origin, urls=None, context=None):
        self.id = id
        self.type = type
        self.name = name
        self.names = {name}
        self.origin = EntityOrigin.create(origin)
        self.urls = urls if urls else []
        self.context = context

    def __repr__(self):
        return "Entity({}, {}, {})".format(self.id, self.name, self.type)

    def __str__(self):
        return "{}\t{}\t{}\t{}".format(self.id, self.name, self.type, ','.join(self.names))


class Mention:
    """
    Entity Mention
    :string id: Unique mention id
    :string string: Mention string (maybe be normalized)
    :string docid: Document id
    :tuple offsets: Character offsets into the original document (1-based index, inclusive)
    :tuple token_offsets: Token offsets into the original document (0-based index, exclusive)
    :string type: Entity type. See EntityType.
    :string original_string: Original mention string from the document
    :string translit_string: Optional transliteration of the string
    :string translate_string: Optional translation of the string
    """
    def __init__(self, string, docid, offsets, token_offsets, type, id=None):
        # id is often assigned after creation
        self.id = id
        self.string = string
        self.docid = docid
        self.offsets = offsets
        self.token_offsets = token_offsets
        self.type = type
        self.original_string = string
        self.translit_string = None
        self.translate_string = None

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


class LinkType:
    NIL = 'NIL'
    LINK = 'link'


class Link:
    def __init__(self, entity_type, link_type, links=None, cluster_id=None, name=None):
        self.entity_type = entity_type
        self.link_type = link_type
        self.links = links
        self.cluster_id = cluster_id
        self.name = name


class Document:
    """
    Document with its tokens and entity mentions
    :list mentions: List of entity mentions
    :list tokens: List of tokens
    :string docid: Doc ID of the original document
    :string type: DocType
    :list mention_chains: List of MentionChain objects
    """

    def __init__(self, mentions, tokens, lang):
        self.mentions = mentions
        self.tokens = tokens
        self.lang = lang
        self.docid = self.mentions[0].docid
        self.type = Document.detect_type(self.docid)
        self.mention_chains = None

    @staticmethod
    def detect_type(doc_id):
        return DocType.detect(doc_id)

    def __repr__(self):
        return "Document({}) with {} mentions".format(self.docid, len(self.mentions))
