import unittest
from hamerkop.preprocessor import *
from hamerkop.core import Document, Mention
from hamerkop.lang import Lang
from hamerkop.string import DictStemmer, DictTranslator


class CascadePreprocessorTest(unittest.TestCase):
    def test(self):
        processors = [Blacklist(['bulgaria', 'africa']), TooLongMentionRemover(4)]
        processor = CascadePreprocessor(processors)
        mentions = [
            Mention('Henry Adams', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy writes long novels', 'doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertNotIn(mentions[1], document.mentions)
        self.assertNotIn(mentions[3], document.mentions)


class TypeValidatorTest(unittest.TestCase):
    def test(self):
        processor = TypeValidator()
        mentions = [
            Mention('Saʼud Arabiyaa', 'doc34', (1, 3), (), EntityType.GPE),
            Mention('Saʼud Arabiyaa', 'doc34', (1, 3), (), 'BGE'),
            Mention('Edward', 'doc34', (1, 3), (), EntityType.PER),
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))


class TextNormalizerTest(unittest.TestCase):
    def test(self):
        processor = TextNormalizer()
        mentions = [
            Mention('bw’Uburayi', 'doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual("bw'Uburayi", document.mentions[0].string)


class GarbageRemoverTest(unittest.TestCase):
    def test_remove_websites(self):
        processor = GarbageRemover()
        mentions = [
            Mention('Henry Adams', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', 'doc34', (1, 3), (), EntityType.PER),
            Mention('http://www.google.com', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', 'doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(3, len(document.mentions))
        self.assertNotIn(mentions[2], document.mentions)


class FixTypeTest(unittest.TestCase):
    def test(self):
        processor = FixType({'africa': EntityType.LOC})
        mentions = [
            Mention('Africa', 'doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual(EntityType.LOC, document.mentions[0].type)


class TooLongMentionRemoverTest(unittest.TestCase):
    def test(self):
        processor = TooLongMentionRemover(3)
        mentions = [
            Mention('Henry J. Adams', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Henry Adams eats mice', 'doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual('Henry J. Adams', document.mentions[0].string)


class BlacklistTest(unittest.TestCase):
    def test(self):
        processor = Blacklist(['bulgaria', 'africa'])
        mentions = [
            Mention('Henry Adams', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', 'doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', 'doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertNotIn(mentions[1], document.mentions)


class AcronymReplacerTest(unittest.TestCase):
    def test_case_sensitive(self):
        processor = AcronymReplacer({'UN': 'United Nations'}, False)
        mentions = [
            Mention('UN', 'IL5_doc34', (1, 3), (), EntityType.GPE),
            Mention('un', 'IL5_doc34', (4, 5), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertEqual('United Nations', document.mentions[0].string)
        self.assertEqual('un', document.mentions[1].string)

    def test_case_insensitive(self):
        processor = AcronymReplacer({'UN': 'United Nations'}, True)
        mentions = [
            Mention('UN', 'IL5_doc34', (1, 3), (), EntityType.GPE),
            Mention('un', 'IL5_doc34', (4, 5), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.EN)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertEqual('United Nations', document.mentions[0].string)
        self.assertEqual('United Nations', document.mentions[1].string)


class NameTranslatorTest(unittest.TestCase):
    def test(self):
        translator = DictTranslator({'Bodensee': 'Lake Constance'})
        processor = NameTranslator(translator)
        mentions = [
            Mention('Bodensee', 'doc34', (1, 3), (), EntityType.GPE),
            Mention('Bulgaria', 'doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.DE)
        processor.process(document)
        self.assertEqual('Lake Constance', mentions[0].string)
        self.assertEqual('Bodensee', mentions[0].native_string)
        self.assertIsNone(mentions[1].native_string)


class NameStemmerTest(unittest.TestCase):
    def test(self):
        stemmer = DictStemmer({'kölner': 'köln'})
        processor = NameStemmer(stemmer)
        mentions = [
            Mention('Kölner Dom', 'doc34', (1, 3), (), EntityType.LOC),
            Mention('Rheinenergiestadion', 'doc34', (1, 3), (), EntityType.LOC),
        ]
        document = Document(mentions, [], Lang.DE)
        processor.process(document)
        self.assertEqual('köln Dom', mentions[0].string)
        self.assertEqual('Rheinenergiestadion', mentions[1].string)
