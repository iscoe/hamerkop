from abc import ABC, abstractmethod


class Preprocessor(ABC):
    """
    A preprocessor runs before coref and candidate generation to filter and clean the mentions.
    """

    @abstractmethod
    def process(self, document):
        """
        Process the mentions in a document
        :param document: Document
        :return: Document
        """
        pass


class PassThru(Preprocessor):
    """Does not change the entity mentions"""
    def process(self, document):
        return document


class CascadePreprocessor(Preprocessor):
    """Run a list of processors on the mentions"""
    def __init__(self, processors):
        """
        :param processors: list of Preprocessor objects
        """
        self.processors = processors

    def process(self, document):
        for processor in self.processors:
            document = processor.process(document)
            if not document:
                return None
        return document
