import unittest
from hamerkop.preprocessor import *
from hamerkop.core import Document, Mention
from hamerkop.lang import Lang
from hamerkop.string import DictStemmer, DictTranslator


class PreprocessorReporterTest(unittest.TestCase):
    class Preprocessor(Preprocessor):
        def process(self, document):
            with pcm().removal(document):
                del document.mentions[1]
            for mention in document.mentions:
                with pcm().modification(mention):
                    mention.string = mention.string + 'test'

    def test_activate(self):
        PreprocessorReporter.activate()
        self.run_preprocessor()
        self.assertEqual(1, len(PreprocessorReporter.report.modifications))
        self.assertEqual(3, list(PreprocessorReporter.report.modifications.values())[0])
        self.assertEqual(1, len(PreprocessorReporter.report.removals))

    def test_deactivate(self):
        PreprocessorReporter.report.clear()
        PreprocessorReporter.deactivate()
        self.run_preprocessor()
        self.assertEqual(0, len(PreprocessorReporter.report.modifications))
        self.assertEqual(0, len(PreprocessorReporter.report.removals))

    def run_preprocessor(self):
        processor = PreprocessorReporterTest.Preprocessor()
        mentions = [
            Mention('Henry Adams', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy writes long novels', '_NW_doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)


class CascadePreprocessorTest(unittest.TestCase):
    def test(self):
        processors = [Blacklist(['bulgaria', 'africa']), TooLongMentionRemover(4)]
        processor = CascadePreprocessor(processors)
        mentions = [
            Mention('Henry Adams', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy writes long novels', '_NW_doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertNotIn(mentions[1], document.mentions)
        self.assertNotIn(mentions[3], document.mentions)


class TypeValidatorTest(unittest.TestCase):
    def test(self):
        processor = TypeValidator()
        mentions = [
            Mention('Saʼud Arabiyaa', '_NW_doc34', (1, 3), (), EntityType.GPE),
            Mention('Saʼud Arabiyaa', '_NW_doc34', (1, 3), (), 'BGE'),
            Mention('Edward', '_NW_doc34', (1, 3), (), EntityType.PER),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))


class TextNormalizerTest(unittest.TestCase):
    def test(self):
        processor = TextNormalizer()
        mentions = [
            Mention('bw’Uburayi', '_NW_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual("bw'Uburayi", document.mentions[0].string)


class GarbageRemoverTest(unittest.TestCase):
    def test_remove_websites(self):
        processor = GarbageRemover()
        mentions = [
            Mention('Henry Adams', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('http://www.google.com', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', '_NW_doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(3, len(document.mentions))
        self.assertNotIn(mentions[2], document.mentions)


class FixTypeTest(unittest.TestCase):
    def test(self):
        processor = FixType({'africa': EntityType.LOC})
        mentions = [
            Mention('Africa', '_NW_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual(EntityType.LOC, document.mentions[0].type)


class TooLongMentionRemoverTest(unittest.TestCase):
    def test(self):
        processor = TooLongMentionRemover(3)
        mentions = [
            Mention('Henry J. Adams', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Henry Adams eats mice', '_NW_doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(1, len(document.mentions))
        self.assertEqual('Henry J. Adams', document.mentions[0].string)


class BlacklistTest(unittest.TestCase):
    def test(self):
        processor = Blacklist(['bulgaria', 'africa'])
        mentions = [
            Mention('Henry Adams', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', '_NW_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', '_NW_doc34', (1, 3), (), EntityType.PER)
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertNotIn(mentions[1], document.mentions)


class AcronymReplacerTest(unittest.TestCase):
    def test_case_sensitive(self):
        processor = AcronymReplacer({'UN': 'United Nations'}, False)
        mentions = [
            Mention('UN', 'IL5_NW_doc34', (1, 3), (), EntityType.GPE),
            Mention('un', 'IL5_NW_doc34', (4, 5), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertEqual('United Nations', document.mentions[0].string)
        self.assertEqual('un', document.mentions[1].string)

    def test_case_insensitive(self):
        processor = AcronymReplacer({'UN': 'United Nations'}, True)
        mentions = [
            Mention('UN', 'IL5_NW_doc34', (1, 3), (), EntityType.GPE),
            Mention('un', 'IL5_NW_doc34', (4, 5), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertEqual('United Nations', document.mentions[0].string)
        self.assertEqual('United Nations', document.mentions[1].string)


class NameProjectorTest(unittest.TestCase):
    def test_translate(self):
        translator = DictTranslator({'Bodensee': 'Lake Constance'})
        processor = NameProjector(translator.translate, NameProjector.TRANSLATE)
        mentions = [
            Mention('Bodensee', '_NW_doc34', (1, 3), (), EntityType.GPE),
            Mention('Bulgaria', '_NW_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.DEU)
        processor.process(document)
        self.assertEqual('Bodensee', mentions[0].string)
        self.assertEqual('Lake Constance', mentions[0].translate_string)
        self.assertIsNone(mentions[0].translit_string)
        self.assertIsNone(mentions[1].translate_string)


class NameStemmerTest(unittest.TestCase):
    def test(self):
        stemmer = DictStemmer({'kölner': 'köln'})
        processor = NameStemmer(stemmer)
        mentions = [
            Mention('Kölner Dom', '_NW_doc34', (1, 3), (), EntityType.LOC),
            Mention('Rheinenergiestadion', '_NW_doc34', (1, 3), (), EntityType.LOC),
        ]
        document = Document(mentions, [], Lang.DEU)
        processor.process(document)
        self.assertEqual('köln Dom', mentions[0].string)
        self.assertEqual('Rheinenergiestadion', mentions[1].string)


class TwitterUsernameReplacerTest(unittest.TestCase):
    def test(self):
        tum = {
            'barney': 'Barney Rubble',
            'fred': 'Fred Flintstone'
        }
        processor = TwitterUsernameReplacer(tum)
        mentions = [
            Mention('@barney', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
            Mention('@fred:', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
            Mention('Bulgaria', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
            Mention('Leo Tolstoy writes long novels', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
            Mention('@', 'IL5_SN_doc34', (1, 3), (), EntityType.PER),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual(6, len(document.mentions))
        self.assertEqual('Barney Rubble', document.mentions[0].string)
        self.assertEqual('Fred Flintstone', document.mentions[1].string)


class TwitterHashtagProcessorTest(unittest.TestCase):
    def test_simple(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#HashTag', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('Hash Tag', document.mentions[0].string)

    def test_empty_tag(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('', document.mentions[0].string)

    def test_includes_numbers(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#Football4Ever', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('Football Ever', document.mentions[0].string)

    def test_no_uppercase_chars(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#egyptian', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('egyptian', document.mentions[0].string)

    def test_start_lowercase_chars(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#egyptianFun', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('egyptian Fun', document.mentions[0].string)

    def test_weird_chars(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#…', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('…', document.mentions[0].string)

    def test_unexpected_char_in_normal_tag(self):
        processor = TwitterHashtagProcessor()
        mentions = [
            Mention('#Ethiopia|n', 'IL5_SN_doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [], Lang.ENG)
        processor.process(document)
        self.assertEqual('Ethiopia n', document.mentions[0].string)
