import logging
import os

from src.utils.utils import check_path_exists
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, RDF
from rdflib.plugins.sparql import prepareQuery

LOGGER = logging.getLogger('l')
HOME_URI = 'http://example.org/'


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

    def save(self, path: str = 'models'):
        check_path_exists(path)
        self.graph.serialize(os.path.join(path, 'store'), format='n3')

    def create_video(self, youtube_id, title):
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        self.graph.add((video_uri, RDF['type'], DC['MovingImage']))
        self.graph.add((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.graph.add((video_uri, DC['title'], Literal(title)))
        self.save()

    def add_entity_to_video(self, entity, youtube_id):
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity}')

        self.graph.add((video_uri, DC['contributor'], entity_uri))
        self.save()

    def video_is_in(self, youtube_id):
        return (URIRef(f'{HOME_URI}{youtube_id}'), RDF['type'], DC['MovingImage']) in self.graph

    def get_videos_of_entity(self, entity):
        q = prepareQuery(
            '''
            SELECT ?url ?title 
            WHERE {
                ?video a dc:MovingImage; 
                    dc:contributor ?entity;
                    dc:identifier ?url; 
                    dc:title ?title.
            }
            ''',
            initNs={'dc': DC}
        )
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity}')
        results = []
        for row in self.graph.query(q, initBindings={'entity': entity_uri}):
            results.append({'link': row[0], 'title': row[1]})
        return results
