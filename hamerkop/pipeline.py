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

    def run(self):
        for doc in self.documents:
            self.preprocessor.process(doc)
            self.coref.coref(doc)
            self.candidate_gen.process(doc)
            self.resolver.resolve(doc)
            self.writer.write(doc)
