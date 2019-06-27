# Copyright 2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import io

from .candidates import CandidatesScorer
from .coref import CorefScorer
from .preprocessor import PreprocessorReporter
from .resolver import ResolverScorer
from .utilities import NotATimer, Timer


class TimeReport:
    def __init__(self, enabled=False):
        if enabled:
            self.main = Timer('main')
            self.preprocessing = Timer('preprocessing')
            self.coref = Timer('coref')
            self.candidates = Timer('candidates')
            self.resolver = Timer('resolver')
        else:
            self.main = NotATimer('main')
            self.preprocessing = NotATimer('preprocessing')
            self.coref = NotATimer('coref')
            self.candidates = NotATimer('candidates')
            self.resolver = NotATimer('resolver')

    @property
    def total_time(self):
        return self.main.time

    def __str__(self):
        buf = io.StringIO()
        buf.write('Timing Profile\n')
        buf.write('--------------\n')
        self.print_line(buf, 'Overall', self.main.time)
        self.print_line(buf, 'Preprocessing', self.preprocessing.time)
        self.print_line(buf, 'Indoc Coref', self.coref.time)
        self.print_line(buf, 'Candidate Gen', self.candidates.time)
        self.print_line(buf, 'Resolution', self.resolver.time)
        return buf.getvalue()

    @staticmethod
    def print_line(buf, name, value):
        buf.write('{: <15} {:.2f}s\n'.format(name + ':', value))


class Report:
    def __init__(self):
        self.time_report = TimeReport()
        self.preprocessor_report = None
        self.coref_report = None
        self.candidates_report = None
        self.resolver_report = None

    def __str__(self):
        buf = io.StringIO()
        if self.time_report.total_time > 0:
            buf.write(str(self.time_report) + '\n')
        reports = [self.preprocessor_report, self.coref_report, self.candidates_report, self.resolver_report]
        for report in reports:
            if report:
                buf.write(str(report) + '\n')
        return buf.getvalue()


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

        self._profiling = False
        self._progress = False
        self._expected_num_docs = 0
        self._progress_period = 0
        self._scoring = False
        self._ground_truth = None
        self._coref_scorer = None
        self._candidates_scorer = None
        self._resolver_scorer = None

    def enable_profiling(self):
        self._profiling = True
        self.report.time_report = TimeReport(enabled=True)

    def enable_scoring(self, ground_truth):
        self._scoring = True
        self._ground_truth = ground_truth
        PreprocessorReporter.activate()
        self._coref_scorer = CorefScorer(self._ground_truth)
        self._candidates_scorer = CandidatesScorer(self._ground_truth)
        self._resolver_scorer = ResolverScorer(self._ground_truth)

    def enable_progress(self, expected_number=0, period=100):
        self._progress = True
        self._expected_num_docs = expected_number
        self._progress_period = period

    def run(self):
        document_count = 0
        with self.report.time_report.main:
            for doc in self.documents:
                # preprocessing
                with self.report.time_report.preprocessing:
                    self.preprocessor.process(doc)

                # indoc coref
                with self.report.time_report.coref:
                    self.coref.coref(doc)
                if self._scoring:
                    self._coref_scorer.update(doc)

                # candidate generation
                with self.report.time_report.candidates:
                    self.candidate_gen.process(doc)
                if self._scoring:
                    self._candidates_scorer.update(doc)

                # resolution
                with self.report.time_report.resolver:
                    self.resolver.resolve(doc)
                if self._scoring:
                    self._resolver_scorer.update(doc)

                # update output file
                self.writer.write(doc)

                document_count += 1
                if self._progress and document_count % self._progress_period == 0:
                    if self._expected_num_docs:
                        m = ' {0: <5} {1: >3}%'.format(document_count, int(100 * document_count / self._expected_num_docs))
                        print(m, end='\r')
                    else:
                        print(' {0: <5}'.format(document_count), end='\r')

        if self._progress:
            if self._profiling:
                print('Processed {0} documents in {1:.2f} sec'.format(document_count, self.report.time_report.main.time))
            else:
                print('Processed {} documents'.format(document_count))

        if self._scoring:
            self.report.preprocessor_report = PreprocessorReporter.report
            self.report.coref_report = self._coref_scorer.report
            self.report.candidates_report = self._candidates_scorer.report
            self.report.resolver_report = self._resolver_scorer.report
