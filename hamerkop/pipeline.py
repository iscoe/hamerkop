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
        self._progress = False
        self._expected_num_docs = 0
        self._progress_period = 0
        self._scoring = False
        self.ground_truth = None
        self.coref_scorer = None

    def enable_scoring(self, ground_truth):
        self._scoring = True
        self.ground_truth = ground_truth
        PreprocessorReporter.activate()
        self.coref_scorer = CorefScorer(self.ground_truth)

    def enable_progress(self, expected_number=0, period=100):
        self._progress = True
        self._expected_num_docs = expected_number
        self._progress_period = period

    def run(self):
        document_count = 0
        for doc in self.documents:
            self.preprocessor.process(doc)
            self.coref.coref(doc)
            if self._scoring:
                self.coref_scorer.update(doc)
            self.candidate_gen.process(doc)
            self.resolver.resolve(doc)
            self.writer.write(doc)
            document_count += 1
            if self._progress and document_count % self._progress_period == 0:
                if self._expected_num_docs:
                    m = ' {0: <5} {1: >3}%'.format(document_count, int(100 * document_count / self._expected_num_docs))
                    print(m, end='\r')
                else:
                    print(' {0: <5}'.format(document_count), end='\r')

        if self._progress:
            print('Processed {} documents'.format(document_count))

        if self._scoring:
            self.report.preprocessor_report = PreprocessorReporter.report
            self.report.coref_report = self.coref_scorer.report
