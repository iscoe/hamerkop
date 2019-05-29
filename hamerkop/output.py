

class OutputWriter:
    """
    Writes a file that conforms to the LoreHLT submission format:
      System Mention Text Doc:Offsets KB_ID Entity_Type Mention_Type Confidence

    Sets the KB_ID to NIL for mentions without a match
    """
    def __init__(self, filename, system, prob=0.1):
        self.filename = filename
        self.system = system
        self.prob = prob
        self.fp = open(self.filename, 'w')

    def close(self):
        self.fp.close()

    def write(self, document):
        for chain in document.mention_chains:
            if chain.entity is None:
                entity = 'NIL'
            else:
                entity = chain.entity.id
            for mention in chain:
                doc_info = "{}:{}-{}".format(mention.docid, *mention.offsets)
                line = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    self.system, mention.id, mention.original_string, doc_info,
                    entity, mention.type, 'NAM', self.prob)
                self.fp.write(line)
