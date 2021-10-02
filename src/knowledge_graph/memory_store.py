import logging
import os

from src.utils.utils import check_path_exists, get_config
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, RDF, Namespace, FOAF, XSD, RDFS
from rdflib.plugins.sparql import prepareQuery

LOGGER = logging.getLogger('memory-store')

on_rtd = os.environ.get('READTHEDOCS') == 'True'

if on_rtd:
    CONFIG = get_config('../src/utils/config.yaml')
else:
    CONFIG = get_config('../src/utils/config.yaml')

HOME_URI = CONFIG['rdf']['uri']

MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')
VIDEO = Namespace('http://purl.org/ontology/video/')
TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/builtins/3.3/temporal.owl')
DBO = Namespace('http://dbpedia.org/ontology/')
DBR = Namespace('http://dbpedia.org/resource/')


class MemoryStore(object):
    """ Implementation to store and query rdf-triples in a local file. """

    def __init__(self, path: str = './models/store'):
        """
        Args:
            path (str): Location where the triples should be saved.
        """
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

        Args:
            triple (tuple): The triple to be saved.
        """
        self.graph.add(triple)

    def commit(self):
        """ Make the changes persistent and available """
        check_path_exists(os.path.split(self.path)[0])
        self.graph.serialize(self.path, format='n3')

    def query(self, query: str) -> list:
        """ Execute a SPARQL query on a local file

        Args:
            query: (str): A valid SPARQL query.

        Returns:
            results (list): Returns a list of lists with the queried properties. Format: [[<property1>, <property2>, ...], ...]
        """
        prepared_query = prepareQuery(query,
                                      initNs={'dc': DC, 'foaf': FOAF, 'video': VIDEO, 'mpeg7': MPEG7, 'dbo': DBO,
                                              'dbr': DBR, 'rdf': RDF, 'rdfs': RDFS, 'temporal': TEMPORAL})
        results = []
        for row in self.graph.query(prepared_query):
            elements = []
            for element in row:
                elements.append(str(element))
            results.append(elements)
        return results

    def exists(self, youtube_id: str) -> bool:
        """ Checks if a video already exists in the graph

        Args:
            youtube_id (str): The id of the video to check.
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        return (video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')) in self.graph
