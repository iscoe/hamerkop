import abc


class Resolver(abc.ABC):
    """Resolve links between mention chains and kb entities"""

    @abc.abstractmethod
    def resolve(self, document):
        """
        Resolve which entity candidate is best from a list of candidates for each mention chain
        :param document: Document with mention chains and candidate sets
        """
        pass
