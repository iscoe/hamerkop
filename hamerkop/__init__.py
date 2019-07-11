# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

__version__ = '0.1.dev'

# core classes and data structures
from .core import Document, DocType, Entity, EntityContext, EntityOrigin, EntityType, Mention, MentionChain

# language detection
from .lang import Lang, LangDetector, FixedLang, NgramLangDetector

# input and output file reading and writing
from .io import InputReader, CoNLLReaderException, OutputWriter, OutputReader, DocumentPreparerUsingGroundTruth, \
    EntityLoader, EntityFilter, CascadeEntityFilter, EntityOriginFilter, EntityLinkFilter, EntityCountryFilter, \
    NameFilter, CascadeNameFilter, ScriptBasedNameFilter, LanguageBasedNameFilter

# knowledge base implementations
from .kb import KB, KBException, MemoryKB, \
    NameIndex, ExactMatchMemoryNameIndex, NgramMemoryNameIndex, \
    KBLoadingScorer

# string utilities
from .string import String, Stemmer, DictStemmer, Translator, DictTranslator, URoman

# general utilities
from .utilities import CaseInsensitiveDict, CaseInsensitiveSet, Identifier, InProcessIncremental, Timer, NotATimer

# 1st stage: preprocessing mentions
from .preprocessor import Preprocessor, PreprocessorReporter, CascadePreprocessor, PassThru, FixType, TypeValidator, \
    TwitterHashtagProcessor, TwitterUsernameReplacer, TextNormalizer, GarbageRemover, TooLongMentionRemover, \
    Blacklist, NameProjector, NameStemmer, AcronymReplacer

# 2nd stage: in document coreference
from .coref import Coref, CascadeCoref, CorefStage, ExactMatchStage, AcronymStage, PersonLastNameStage

# 3rd stage: candidate generation
from .candidates import CandidateGenerator, IndexBasedGenerator, CombiningGenerator, CachingGenerator, CascadeGenerator

# 4th stage: entity resolution
from .resolver import Resolver, CascadeResolver, FirstResolver, ExactNameResolver, WikipediaResolver

from .pipeline import Pipeline
