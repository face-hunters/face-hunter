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
        """ Saves the RDF-graph locally

        Parameters
        ----------
        path: str
            Path where the graph should be saved
        """
        check_path_exists(path)
        self.graph.serialize(os.path.join(path, 'store'), format='n3')

    def create_video(self, youtube_id: str, title: str):
        """ Checks if all entities from the information.csv are in the entity-list

        Parameters
        ----------
        youtube_id: str
            Id of a youtube video to be linked
        title: str
            The title of the youtube video
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        self.graph.add((video_uri, RDF['type'], DC['MovingImage']))
        self.graph.add((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.graph.add((video_uri, DC['title'], Literal(title)))
        self.save()

    def add_entity_to_video(self, entity: str, youtube_id: str):
        """ Creates the link between an entity and a video from youtube

        Parameters
        ----------
        entity: str
            Name of the entity
        youtube_id: str
            Id of a youtube video to be linked
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity}')

        self.graph.add((video_uri, DC['contributor'], entity_uri))
        self.save()

    def video_is_in(self, youtube_id: str):
        """ Checks if a video is already included in the rdf-graph

        Parameters
        ----------
        youtube_id: str
            Id of a youtube video to search for

        Returns
        ----------
        Boolean
            Whether a video exists in the graph or not
        """
        return (URIRef(f'{HOME_URI}{youtube_id}'), RDF['type'], DC['MovingImage']) in self.graph

    def get_videos_of_entity(self, entity: str):
        """ Searches for videos of an entity

        Parameters
        ----------
        entity: str
            Name of the entity to look for

        Returns
        ----------
        List
            Returns a list of the videos in which a entity occurs. Type: [{url: <example>, title: <example>}, ...]
        """
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
            results.append({'url': row[0], 'title': row[1]})
        return results
