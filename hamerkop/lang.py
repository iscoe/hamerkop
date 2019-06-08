from abc import ABC, abstractmethod
import enum
import langdetect


class Lang(enum.Enum):
    """
    Language enumeration

    ISO 639-1 language codes
    """

    AB = 'Abkhaz'
    AA = 'Afar'
    AF = 'Afrikaans'
    AK = 'Akan'
    SQ = 'Albanian'
    AM = 'Amharic'
    AR = 'Arabic'
    AN = 'Aragonese'
    HY = 'Armenian'
    AS = 'Assamese'
    AV = 'Avaric'
    AE = 'Avestan'
    AY = 'Aymara'
    AZ = 'Azerbaijani'
    BM = 'Bambara'
    BA = 'Bashkir'
    EU = 'Basque'
    BE = 'Belarusian'
    BN = 'Bengali'
    BH = 'Bihari'
    BI = 'Bislama'
    BS = 'Bosnian'
    BR = 'Breton'
    BG = 'Bulgarian'
    MY = 'Burmese'
    CA = 'Catalan'
    CH = 'Chamorro'
    CE = 'Chechen'
    NY = 'Chichewa; Chewa; Nyanja'
    ZH = 'Chinese'
    CV = 'Chuvash'
    KW = 'Cornish'
    CO = 'Corsican'
    CR = 'Cree'
    HR = 'Croatian'
    CS = 'Czech'
    DA = 'Danish'
    DV = 'Maldivian;'
    NL = 'Dutch'
    DZ = 'Dzongkha'
    EN = 'English'
    EO = 'Esperanto'
    ET = 'Estonian'
    EE = 'Ewe'
    FO = 'Faroese'
    FJ = 'Fijian'
    FI = 'Finnish'
    FR = 'French'
    FF = 'Fula'
    GL = 'Galician'
    KA = 'Georgian'
    DE = 'German'
    EL = 'Greek: Modern'
    GN = 'Guaraní'
    GU = 'Gujarati'
    HT = 'Haitian'
    HA = 'Hausa'
    HE = 'Hebrew'
    HZ = 'Herero'
    HI = 'Hindi'
    HO = 'Hiri Motu'
    HU = 'Hungarian'
    IA = 'Interlingua'
    ID = 'Indonesian'
    IE = 'Interlingue'
    GA = 'Irish'
    IG = 'Igbo'
    IK = 'Inupiaq'
    IO = 'Ido'
    IS = 'Icelandic'
    IT = 'Italian'
    IU = 'Inuktitut'
    JA = 'Japanese'
    JV = 'Javanese'
    KL = 'Kalaallisut'
    KN = 'Kannada'
    KR = 'Kanuri'
    KS = 'Kashmiri'
    KK = 'Kazakh'
    KM = 'Khmer'
    KI = 'Kikuyu: Gikuyu'
    RW = 'Kinyarwanda'
    KY = 'Kyrgyz'
    KV = 'Komi'
    KG = 'Kongo'
    KO = 'Korean'
    KU = 'Kurdish'
    KJ = 'Kwanyama'
    LA = 'Latin'
    LB = 'Luxembourgish'
    LG = 'Luganda'
    LI = 'Limburgish'
    LN = 'Lingala'
    LO = 'Lao'
    LT = 'Lithuanian'
    LU = 'Luba-Katanga'
    LV = 'Latvian'
    GV = 'Manx'
    MK = 'Macedonian'
    MG = 'Malagasy'
    MS = 'Malay'
    ML = 'Malayalam'
    MT = 'Maltese'
    MI = 'Māori'
    MR = 'Marathi'
    MH = 'Marshallese'
    MN = 'Mongolian'
    NA = 'Nauru'
    NV = 'Navajo'
    NB = 'Norwegian Bokmål'
    ND = 'North Ndebele'
    NE = 'Nepali'
    NG = 'Ndonga'
    NN = 'Norwegian Nynorsk'
    NO = 'Norwegian'
    II = 'Nuosu'
    NR = 'South Ndebele'
    OC = 'Occitan'
    OJ = 'Ojibwe'
    CU = 'Old Church Slavonic'
    OM = 'Oromo'
    OR = 'Oriya'
    OS = 'Ossetian: Ossetic'
    PA = 'Panjabi: Punjabi'
    PI = 'Pāli'
    FA = 'Persian'
    PL = 'Polish'
    PS = 'Pashto'
    PT = 'Portuguese'
    QU = 'Quechua'
    RM = 'Romansh'
    RN = 'Kirundi'
    RO = 'Romanian'
    RU = 'Russian'
    SA = 'Sanskrit'
    SC = 'Sardinian'
    SD = 'Sindhi'
    SE = 'Northern Sami'
    SM = 'Samoan'
    SG = 'Sango'
    SR = 'Serbian'
    GD = 'Scottish Gaelic'
    SN = 'Shona'
    SI = 'Sinhala'
    SK = 'Slovak'
    SL = 'Slovene'
    SO = 'Somali'
    ST = 'Southern Sotho'
    ES = 'Spanish'
    SU = 'Sundanese'
    SW = 'Swahili'
    SS = 'Swati'
    SV = 'Swedish'
    TA = 'Tamil'
    TE = 'Telugu'
    TG = 'Tajik'
    TH = 'Thai'
    TI = 'Tigrinya'
    BO = 'Tibetan'
    TK = 'Turkmen'
    TL = 'Tagalog'
    TN = 'Tswana'
    TO = 'Tonga'
    TR = 'Turkish'
    TS = 'Tsonga'
    TT = 'Tatar'
    TW = 'Twi'
    TY = 'Tahitian'
    UG = 'Uyghur'
    UK = 'Ukrainian'
    UR = 'Urdu'
    UZ = 'Uzbek'
    VE = 'Venda'
    VI = 'Vietnamese'
    VO = 'Volapük'
    WA = 'Walloon'
    CY = 'Welsh'
    WO = 'Wolof'
    FY = 'Western Frisian'
    XH = 'Xhosa'
    YI = 'Yiddish'
    YO = 'Yoruba'
    ZA = 'Zhuang'
    ZU = 'Zulu'

    @classmethod
    def from_code(cls, code):
        try:
            return getattr(cls, code.upper())
        except AttributeError:
            return None


class LangDetector(ABC):
    @abstractmethod
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
