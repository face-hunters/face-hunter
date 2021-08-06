import logging
import os

from src.utils.utils import check_path_exists
from rdflib import Graph
from rdflib.namespace import DC, RDF, Namespace, FOAF, XSD, RDFS
from rdflib.plugins.sparql import prepareQuery

LOGGER = logging.getLogger('memory-store')

MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')
VIDEO = Namespace('http://purl.org/ontology/video/')
TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/builtins/3.3/temporal.owl')
DBO = Namespace('http://dbpedia.org/ontology/')
DBR = Namespace('http://dbpedia.org/resource/')


class MemoryStore(object):
    """
    Local Store

    Implementation to store and query rdf-triples locally in a file.

    """
    def __init__(self, path: str = './models/store'):
        self.path = path
        self.graph = Graph()
        if os.path.isfile(self.path):
            self.graph.parse(self.path, format='n3')
        else:
            self.graph.bind('dc', DC)
            self.graph.bind('foaf', FOAF)
            self.graph.bind('xsd', XSD)
            self.graph.bind('video', VIDEO)
            self.graph.bind('mpeg7', MPEG7)
            self.graph.bind('temporal', TEMPORAL)

    def insert(self, triple: tuple):
        """ Add a triple to the knowledge graph

        Parameters
        ----------
        triple: tuple
            The triple to save.
        """
        self.graph.add(triple)

    def commit(self):
        """ Make the changes persistent and available
        """
        check_path_exists(os.path.split(self.path)[0])
        self.graph.serialize(self.path, format='n3')

    def query(self, query: str):
        """ Execute a SPARQL query on a local file

        Parameters
        ----------
        query: str
            A valid SPARQL query.

        Returns
        ----------
        results: List
            Returns a list of lists with the queried properties. Format: [[<property1>, <property2>, ...], ...]
        """
        prepared_query = prepareQuery(query,
                                      initNs={'dc': DC, 'foaf': FOAF, 'video': VIDEO, 'mpeg7': MPEG7, 'dbo': DBO,
                                              'dbr': DBR, 'rdf': RDF, 'rdfs': RDFS})
        results = []
        for row in self.graph.query(prepared_query):
            elements = []
            for element in row:
                elements.append(str(element))
            results.append(elements)
        return results
