import logging
import os

from src.utils.utils import check_path_exists
from rdflib import Graph, URIRef, Namespace, Literal, XSD
from rdflib.namespace import DC, RDF, FOAF
from rdflib.plugins.sparql import prepareQuery

LOGGER = logging.getLogger('l')

TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/built-ins/3.3/temporal.owl')
MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')


class Database(object):
    """
    Store

    Links new videos with their entities in the knowledge graph and allows to look up user queries.

    """
    def __init__(self):
        self.graph = Graph()
        if os.path.isfile('models/store'):
            self.graph.parse('models/store', format='n3')
        else:
            self.graph.bind('dc', DC)
            self.graph.bind('mpeg7', MPEG7)
            self.graph.bind('temporal', TEMPORAL)
            self.graph.bind('foaf', FOAF)

    def save(self, path: str = 'models'):
        check_path_exists(path)
        self.graph.serialize(os.path.join(path, 'store'), format='n3')

    def create_video(self, youtube_id, title):
        video_uri = URIRef(f'http://localhost/{youtube_id}')
        self.graph.add((video_uri, RDF['type'], MPEG7['Video']))
        self.graph.add((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.graph.add((video_uri, DC['title'], Literal(title)))
        self.save()

    def add_entity_to_video(self, entity, youtube_id, time_range):
        video_uri = URIRef(f'http://localhost/{youtube_id}')
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity}')
        scene_uri = URIRef('http://localhost/scene/2')

        self.graph.add((scene_uri, RDF['type'], DC['PeriodOfTime']))
        self.graph.add((video_uri, DC['hasPart'], scene_uri))
        self.graph.add((scene_uri, TEMPORAL['hasStartTime'], Literal(time_range[0], datatype=XSD['time'])))
        self.graph.add((scene_uri, TEMPORAL['hasFinishTime'], Literal(time_range[1], datatype=XSD['time'])))
        self.graph.add((scene_uri, FOAF['depicts'], entity_uri))
        self.save()

    def video_is_in(self, youtube_id):
        return (URIRef(f'http://localhost/{youtube_id}'), RDF['type'], MPEG7['Video']) in self.graph

    def get_videos_of_entity(self, entity):
        q = prepareQuery(
            '''
            SELECT ?url ?title 
            WHERE {
                ?video a mpeg7:Video; 
                    dc:identifier ?url; 
                    dc:title ?title; 
                    dc:hasPart ?part. 
                ?part foaf:depicts ?entity
            }
            ''',
            initNs={'mpeg7': MPEG7, 'dc': DC, 'foaf': FOAF}
        )
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity}')
        results = []
        for row in self.graph.query(q, initBindings={'entity': entity_uri}):
            results.append({'link': row[0], 'title': row[1]})
        return results
