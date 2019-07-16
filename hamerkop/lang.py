# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import abc
import enum
import langdetect

# ISO 639-1 to 639-3 mapping
ISO_MAPPING = {
    'ab': 'abk',
    'aa': 'aar',
    'af': 'afr',
    'ak': 'aka',
    'sq': 'sqi',
    'am': 'amh',
    'ar': 'ara',
    'an': 'arg',
    'hy': 'hye',
    'as': 'asm',
    'av': 'ava',
    'ae': 'ave',
    'ay': 'aym',
    'az': 'aze',
    'bm': 'bam',
    'ba': 'bak',
    'eu': 'eus',
    'be': 'bel',
    'bn': 'ben',
    'bh': 'bih',
    'bi': 'bis',
    'bs': 'bos',
    'br': 'bre',
    'bg': 'bul',
    'my': 'mya',
    'ca': 'cat',
    'ch': 'cha',
    'ce': 'che',
    'ny': 'nya',
    'zh': 'zho',
    'cv': 'chv',
    'kw': 'cor',
    'co': 'cos',
    'cr': 'cre',
    'hr': 'hrv',
    'cs': 'ces',
    'da': 'dan',
    'dv': 'div',
    'nl': 'nld',
    'dz': 'dzo',
    'en': 'eng',
    'eo': 'epo',
    'et': 'est',
    'ee': 'ewe',
    'fo': 'fao',
    'fj': 'fij',
    'fi': 'fin',
    'fr': 'fra',
    'ff': 'ful',
    'gl': 'glg',
    'ka': 'kat',
    'de': 'deu',
    'el': 'ell',
    'gn': 'grn',
    'gu': 'guj',
    'ht': 'hat',
    'ha': 'hau',
    'he': 'heb',
    'hz': 'her',
    'hi': 'hin',
    'ho': 'hmo',
    'hu': 'hun',
    'ia': 'ina',
    'id': 'ind',
    'ie': 'ile',
    'ga': 'gle',
    'ig': 'ibo',
    'ik': 'ipk',
    'io': 'ido',
    'is': 'isl',
    'it': 'ita',
    'iu': 'iku',
    'ja': 'jpn',
    'jv': 'jav',
    'kl': 'kal',
    'kn': 'kan',
    'kr': 'kau',
    'ks': 'kas',
    'kk': 'kaz',
    'km': 'khm',
    'ki': 'kik',
    'rw': 'kin',
    'ky': 'kir',
    'kv': 'kom',
    'kg': 'kon',
    'ko': 'kor',
    'ku': 'kur',
    'kj': 'kua',
    'la': 'lat',
    'lb': 'ltz',
    'lg': 'lug',
    'li': 'lim',
    'ln': 'lin',
    'lo': 'lao',
    'lt': 'lit',
    'lu': 'lub',
    'lv': 'lav',
    'gv': 'glv',
    'mk': 'mkd',
    'mg': 'mlg',
    'ms': 'msa',
    'ml': 'mal',
    'mt': 'mlt',
    'mi': 'mri',
    'mr': 'mar',
    'mh': 'mah',
    'mn': 'mon',
    'na': 'nau',
    'nv': 'nav',
    'nb': 'nob',
    'nd': 'nde',
    'ne': 'nep',
    'ng': 'ndo',
    'nn': 'nno',
    'no': 'nor',
    'ii': 'iii',
    'nr': 'nbl',
    'oc': 'oci',
    'oj': 'oji',
    'cu': 'chu',
    'om': 'orm',
    'or': 'ori',
    'os': 'oss',
    'pa': 'pan',
    'pi': 'pli',
    'fa': 'fas',
    'pl': 'pol',
    'ps': 'pus',
    'pt': 'por',
    'qu': 'que',
    'rm': 'roh',
    'rn': 'run',
    'ro': 'ron',
    'ru': 'rus',
    'sa': 'san',
    'sc': 'srd',
    'sd': 'snd',
    'se': 'sme',
    'sm': 'smo',
    'sg': 'sag',
    'sr': 'srp',
    'gd': 'gla',
    'sn': 'sna',
    'si': 'sin',
    'sk': 'slk',
    'sl': 'slv',
    'so': 'som',
    'st': 'sot',
    'es': 'spa',
    'su': 'sun',
    'sw': 'swa',
    'ss': 'ssw',
    'sv': 'swe',
    'ta': 'tam',
    'te': 'tel',
    'tg': 'tgk',
    'th': 'tha',
    'ti': 'tir',
    'bo': 'bod',
    'tk': 'tuk',
    'tl': 'tgl',
    'tn': 'tsn',
    'to': 'ton',
    'tr': 'tur',
    'ts': 'tso',
    'tt': 'tat',
    'tw': 'twi',
    'ty': 'tah',
    'ug': 'uig',
    'uk': 'ukr',
    'ur': 'urd',
    'uz': 'uzb',
    've': 'ven',
    'vi': 'vie',
    'vo': 'vol',
    'wa': 'wln',
    'cy': 'cym',
    'wo': 'wol',
    'fy': 'fry',
    'xh': 'xho',
    'yi': 'yid',
    'yo': 'yor',
    'za': 'zha',
    'zu': 'zul',
}


class Lang(enum.Enum):
    """
    Language enumeration

    ISO 639-3 language codes
    """
    ABK = 'Abkhaz'
    AAR = 'Afar'
    AFR = 'Afrikaans'
    AKA = 'Akan'
    SQI = 'Albanian'
    AMH = 'Amharic'
    ARA = 'Arabic'
    ARG = 'Aragonese'
    HYE = 'Armenian'
    ASM = 'Assamese'
    AVA = 'Avaric'
    AVE = 'Avestan'
    AYM = 'Aymara'
    AZE = 'Azerbaijani'
    BAM = 'Bambara'
    BAK = 'Bashkir'
    EUS = 'Basque'
    BEL = 'Belarusian'
    BEN = 'Bengali'
    BIH = 'Bihari'
    BIS = 'Bislama'
    BOS = 'Bosnian'
    BRE = 'Breton'
    BUL = 'Bulgarian'
    MYA = 'Burmese'
    CAT = 'Catalan'
    CHA = 'Chamorro'
    CHE = 'Chechen'
    NYA = 'Chichewa'
    ZHO = 'Chinese'
    CHV = 'Chuvash'
    COR = 'Cornish'
    COS = 'Corsican'
    CRE = 'Cree'
    HRV = 'Croatian'
    CES = 'Czech'
    DAN = 'Danish'
    DIV = 'Maldivian;'
    NLD = 'Dutch'
    DZO = 'Dzongkha'
    ENG = 'English'
    EPO = 'Esperanto'
    EST = 'Estonian'
    EWE = 'Ewe'
    FAO = 'Faroese'
    FIJ = 'Fijian'
    FIN = 'Finnish'
    FRA = 'French'
    FUL = 'Fula'
    GLG = 'Galician'
    KAT = 'Georgian'
    DEU = 'German'
    ELL = 'Greek'
    GRN = 'Guaraní'
    GUJ = 'Gujarati'
    HAT = 'Haitian'
    HAU = 'Hausa'
    HEB = 'Hebrew'
    HER = 'Herero'
    HIN = 'Hindi'
    HMO = 'Hiri Motu'
    HUN = 'Hungarian'
    INA = 'Interlingua'
    IND = 'Indonesian'
    ILE = 'Interlingue'
    GLE = 'Irish'
    IBO = 'Igbo'
    IPK = 'Inupiaq'
    IDO = 'Ido'
    ISL = 'Icelandic'
    ITA = 'Italian'
    IKU = 'Inuktitut'
    JPN = 'Japanese'
    JAV = 'Javanese'
    KAL = 'Kalaallisut'
    KAN = 'Kannada'
    KAU = 'Kanuri'
    KAS = 'Kashmiri'
    KAZ = 'Kazakh'
    KHM = 'Khmer'
    KIK = 'Kikuyu'
    KIN = 'Kinyarwanda'
    KIR = 'Kyrgyz'
    KOM = 'Komi'
    KON = 'Kongo'
    KOR = 'Korean'
    KUR = 'Kurdish'
    KUA = 'Kwanyama'
    LAT = 'Latin'
    LTZ = 'Luxembourgish'
    LUG = 'Luganda'
    LIM = 'Limburgish'
    LIN = 'Lingala'
    LAO = 'Lao'
    LIT = 'Lithuanian'
    LUB = 'Luba-Katanga'
    LAV = 'Latvian'
    GLV = 'Manx'
    MKD = 'Macedonian'
    MLG = 'Malagasy'
    MSA = 'Malay'
    MAL = 'Malayalam'
    MLT = 'Maltese'
    MRI = 'Māori'
    MAR = 'Marathi'
    MAH = 'Marshallese'
    MON = 'Mongolian'
    NAU = 'Nauru'
    NAV = 'Navajo'
    NOB = 'Norwegian Bokmål'
    NDE = 'North Ndebele'
    NEP = 'Nepali'
    NDO = 'Ndonga'
    NNO = 'Norwegian Nynorsk'
    NOR = 'Norwegian'
    III = 'Nuosu'
    NBL = 'South Ndebele'
    OCI = 'Occitan'
    OJI = 'Ojibwe'
    CHU = 'Old Church Slavonic'
    ORM = 'Oromo'
    ORI = 'Oriya'
    OSS = 'Ossetian'
    PAN = 'Panjabi'
    PLI = 'Pāli'
    FAS = 'Persian'
    POL = 'Polish'
    PUS = 'Pashto'
    POR = 'Portuguese'
    QUE = 'Quechua'
    ROH = 'Romansh'
    RUN = 'Kirundi'
    RON = 'Romanian'
    RUS = 'Russian'
    SAN = 'Sanskrit'
    SRD = 'Sardinian'
    SND = 'Sindhi'
    SME = 'Northern Sami'
    SMO = 'Samoan'
    SAG = 'Sango'
    SRP = 'Serbian'
    GLA = 'Scottish Gaelic'
    SNA = 'Shona'
    SIN = 'Sinhala'
    SLK = 'Slovak'
    SLV = 'Slovene'
    SOM = 'Somali'
    SOT = 'Southern Sotho'
    SPA = 'Spanish'
    SUN = 'Sundanese'
    SWA = 'Swahili'
    SSW = 'Swati'
    SWE = 'Swedish'
    TAM = 'Tamil'
    TEL = 'Telugu'
    TGK = 'Tajik'
    THA = 'Thai'
    TIR = 'Tigrinya'
    BOD = 'Tibetan'
    TUK = 'Turkmen'
    TGL = 'Tagalog'
    TSN = 'Tswana'
    TON = 'Tonga'
    TUR = 'Turkish'
    TSO = 'Tsonga'
    TAT = 'Tatar'
    TWI = 'Twi'
    TAH = 'Tahitian'
    UIG = 'Uyghur'
    UKR = 'Ukrainian'
    URD = 'Urdu'
    UZB = 'Uzbek'
    VEN = 'Venda'
    VIE = 'Vietnamese'
    VOL = 'Volapük'
    WLN = 'Walloon'
    CYM = 'Welsh'
    WOL = 'Wolof'
    FRY = 'Western Frisian'
    XHO = 'Xhosa'
    YID = 'Yiddish'
    YOR = 'Yoruba'
    ZHA = 'Zhuang'
    ZUL = 'Zulu'

    @classmethod
    def from_code(cls, code):
        if code.lower() in ISO_MAPPING:
            code = ISO_MAPPING[code.lower()]
        try:
            return getattr(cls, code.upper())
        except AttributeError:
            return None


class LangDetector(abc.ABC):
    @abc.abstractmethod
    def detect(self, filename, tokens):
        """
        Detect language from text
        :param filename: local filename which might have language information in it
        :param tokens: list of string tokens
        :return Lang enum or None
        """
        pass


class FixedLang(LangDetector):
    """Hard coded language"""
    def __init__(self, lang):
        self.lang = lang

    def detect(self, filename, tokens):
        return self.lang


class NgramLangDetector(LangDetector):
    """
    Ngram-based language profiles from Wikipedia
    """
    def __init__(self):
        self.factory = langdetect.DetectorFactory()
        self.factory.load_profile(langdetect.PROFILES_DIRECTORY)

    def detect(self, filename, tokens):
        if len(tokens) == 0:
            return None
        detector = self.factory.create()
        detector.append(' '.join(tokens))
        code = detector.detect()
        if code in ('zh-cn', 'zh-tw'):
            code = 'zh'
        return Lang.from_code(code)
