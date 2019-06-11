from .coref import CorefScorer
from .preprocessor import PreprocessorReporter


class Report:
    def __init__(self):
        self.preprocessor_report = None
        self.coref_report = None


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
        self.report = Report()

        self.profiling = False
        self.progress = False
        self._scoring = False
        self.ground_truth = None
        self.coref_scorer = None

    def enable_scoring(self, ground_truth):
        self._scoring = True
        self.ground_truth = ground_truth
        PreprocessorReporter.activate()
        self.coref_scorer = CorefScorer(self.ground_truth)

    def run(self):
        for doc in self.documents:
            self.preprocessor.process(doc)
            self.coref.coref(doc)
            if self._scoring:
                self.coref_scorer.update(doc)
            self.candidate_gen.process(doc)
            self.resolver.resolve(doc)
            self.writer.write(doc)

        if self._scoring:
            self.report.preprocessor_report = PreprocessorReporter.report
            self.report.coref_report = self.coref_scorer.report
