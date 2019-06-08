import unittest
from hamerkop.preprocessor import *
from hamerkop.core import Document, Mention


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
        document = Document(mentions, [])
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
        document = Document(mentions, [])
        processor.process(document)
        self.assertEqual(2, len(document.mentions))


class TextNormalizerTest(unittest.TestCase):
    def test(self):
        processor = TextNormalizer()
        mentions = [
            Mention('bw’Uburayi', 'doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [])
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
        document = Document(mentions, [])
        processor.process(document)
        self.assertEqual(3, len(document.mentions))
        self.assertNotIn(mentions[2], document.mentions)


class FixTypeTest(unittest.TestCase):
    def test(self):
        processor = FixType({'africa': EntityType.LOC})
        mentions = [
            Mention('Africa', 'doc34', (1, 3), (), EntityType.GPE),
        ]
        document = Document(mentions, [])
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
        document = Document(mentions, [])
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
        document = Document(mentions, [])
        processor.process(document)
        self.assertEqual(2, len(document.mentions))
        self.assertNotIn(mentions[1], document.mentions)