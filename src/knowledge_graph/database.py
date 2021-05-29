import logging
import os
from datetime import timedelta
from src.utils.utils import check_path_exists
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DC, RDF, Namespace, FOAF, XSD, OWL
from rdflib.plugins.sparql import prepareQuery

LOGGER = logging.getLogger('l')
HOME_URI = 'http://example.org/'

MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')
VIDEO = Namespace('http://purl.org/ontology/video/')
TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/builtins/3.3/temporal.owl')


class Database(object):
    """
    Store

    Links new videos with their entities in the knowledge graph and allows to look up user queries.
    The data format is based on the paper: https://www.tandfonline.com/doi/full/10.1080/24751839.2018.1437696

    """
    def __init__(self, path: str = 'models/store'):
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

    def save(self):
        """ Saves the RDF-graph locally

        Parameters
        ----------
        path: str
            Path where the graph should be saved
        """
        check_path_exists(os.path.split(self.path)[0])
        self.graph.serialize(self.path, format='n3')

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
        self.graph.add((video_uri, RDF['type'], MPEG7['Video']))
        self.graph.add((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.graph.add((video_uri, DC['title'], Literal(title)))
        self.save()

    def add_scene(self, entities: list, youtube_id: str, start_time: timedelta, end_time: timedelta):
        """ Creates the link between an entity and a video from youtube

        Parameters
        ----------
        entities: list
            Names of the occurring entities
        youtube_id: str
            Id of a youtube video to be linked
        start_time: time
            Start time of the scene in the respective video
        end_time: time
            End time of the scene in the respective video
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        scene_uri = URIRef(f'{HOME_URI}{youtube_id}#t={str(start_time)},{str(end_time)}')

        self.graph.add((scene_uri, RDF['type'], VIDEO['Scene']))
        self.graph.add((scene_uri, VIDEO['sceneFrom'], video_uri))
        self.graph.add((scene_uri, VIDEO['temporalSegmentOf'], video_uri))
        self.graph.add((scene_uri, TEMPORAL['hasStartTime'], Literal(str(start_time), datatype=XSD['dateTime'])))
        self.graph.add((scene_uri, TEMPORAL['duration'], Literal(str(end_time - start_time), datatype=XSD['duration'])))
        self.graph.add((scene_uri, TEMPORAL['hasFinishTime'], Literal(str(end_time), datatype=XSD['dateTime'])))
        for entity in entities:
            entity_uri_dbpedia = URIRef(f'http://dbpedia.org/resource/{entity.replace(" ", "_")}')
            self.graph.add((scene_uri, FOAF['depicts'], entity_uri_dbpedia))
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
            SELECT DISTINCT ?link ?title 
            WHERE {
                ?scene a video:Scene; 
                    foaf:depicts ?entity;
                    video:sceneFrom ?video.
                ?video a mpeg7:Video;
                    dc:identifier ?link;
                    dc:title ?title.
            }
            ''',
            initNs={'dc': DC, 'foaf': FOAF, 'video': VIDEO, 'mpeg7': MPEG7}
        )
        entity_uri = URIRef(f'http://dbpedia.org/resource/{entity.replace(" ", "_")}')
        results = []
        for row in self.graph.query(q, initBindings={'entity': entity_uri}):
            results.append({'url': str(row[0]), 'title': str(row[1])})
        return results
