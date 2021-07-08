import logging
from datetime import timedelta
from rdflib import URIRef, Literal
from rdflib.namespace import DC, RDF, Namespace, FOAF, XSD
from src.knowledge_graph.memory_store import MemoryStore
from src.knowledge_graph.virtuoso_store import VirtuosoStore
from src.utils.utils import get_config

LOGGER = logging.getLogger('graph')
CONFIG = get_config()

HOME_URI = CONFIG['rdf']['uri']

MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')
VIDEO = Namespace('http://purl.org/ontology/video/')
TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/builtins/3.3/temporal.owl')
DBO = Namespace('http://dbpedia.org/ontology/')
DBR = Namespace('http://dbpedia.org/resource/')


class Graph(object):
    """
    Store

    Links new videos with their entities in the knowledge graph and allows to look up user queries.
    The data format is based on the paper: https://www.tandfonline.com/doi/full/10.1080/24751839.2018.1437696

    """
    def __init__(self, storage_type: str = 'memory',
                 memory_path: str = 'models/store',
                 virtuoso_url: str = None,
                 virtuoso_graph: str = None,
                 virtuoso_username: str = None,
                 virtuoso_password: str = None):
        if storage_type == 'memory':
            self.store = MemoryStore(memory_path)
        elif storage_type == 'virtuoso':
            self.store = VirtuosoStore(virtuoso_url, virtuoso_graph, virtuoso_username, virtuoso_password)
        else:
            raise Exception('Unknown storage type')

    def insert_video(self, youtube_id: str, title: str):
        """ Creates the rdf triples for a new video.

        Parameters
        ----------
        youtube_id: str
            Id of a youtube video to be linked.
            For example a4T5ylNQk6g for https://www.youtube.com/watch?v=a4T5ylNQk6g.
        title: str
            The title of the youtube video.
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')

        self.store.insert((video_uri, RDF['type'], MPEG7['Video']))
        self.store.insert((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.store.insert((video_uri, DC['title'], Literal(title)))
        self.store.commit()

    def insert_scene(self, entities: list, youtube_id: str, start_time: timedelta, end_time: timedelta):
        """ Creates the link between an entity and a video from youtube.

        Parameters
        ----------
        entities: list
            Names of the occurring entities.
        youtube_id: str
            Id of a youtube video to be linked.
            For example a4T5ylNQk6g for https://www.youtube.com/watch?v=a4T5ylNQk6g.
        start_time: timedelta
            Start time of the scene in the respective video.
        end_time: timedelta
            End time of the scene in the respective video.
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        scene_uri = URIRef(f'{HOME_URI}{youtube_id}#t={str(start_time)},{str(end_time)}')

        self.store.insert((scene_uri, RDF['type'], VIDEO['Scene']))
        self.store.insert((scene_uri, VIDEO['sceneFrom'], video_uri))
        self.store.insert((scene_uri, VIDEO['temporalSegmentOf'], video_uri))
        self.store.insert((scene_uri, TEMPORAL['hasStartTime'], Literal(str(start_time).split('.', 2)[0],
                                                                        datatype=XSD['dateTime'])))
        self.store.insert(
            (scene_uri, TEMPORAL['duration'], Literal(str(end_time - start_time).split('.', 2)[0],
                                                      datatype=XSD['duration'])))
        self.store.insert((scene_uri, TEMPORAL['hasFinishTime'], Literal(str(end_time).split('.', 2)[0],
                                                                         datatype=XSD['dateTime'])))
        for entity in entities:
            entity_uri_dbpedia = URIRef(f'http://dbpedia.org/resource/{entity.replace(" ", "_")}')
            self.store.insert((scene_uri, FOAF['depicts'], entity_uri_dbpedia))
        self.store.commit()

    def video_exists(self, youtube_id: str) -> bool:
        """ Returns whether a video is already in the graph or not

        Parameters
        ----------
        youtube_id: str
            Id of the YouTube-Video.

        Returns
        ----------
        Boolean
            Whether it exists or not.
        """
        query = ('SELECT COUNT(?video)'
                 'WHERE {'
                 '?video a mpeg7:Video ;'
                 f'dc:identifier "http://www.youtube.com/watch?v={youtube_id}" .'
                 '}')
        return True if int(self.store.query(query)[0][0]) > 0 else False

    def get_videos_with_entity_name(self, entity: str):
        """ Returns all videos for an entity

        Parameters
        ----------
        entity: str
            Name of the entity.

        Returns
        ----------
        List
            Returns a list of the videos in which a entity occurs. Format: [[<link>, <title>], ...]
        """
        query = ('SELECT DISTINCT ?link ?title'
                 'WHERE {'
                 '?scene a video:Scene ;'
                 f'foaf:depicts <http://dbpedia.org/resource/{entity.replace(" ", "_")}> ;'
                 'video:sceneFrom ?video .'
                 '?video a mpeg7:Video ;'
                 'dc:identifier ?link ;'
                 'dc:title ?title .'
                 '}')
        return self.store.query(query)

    def get_videos_with_dbpedia_data(self, filters: dict):
        """ Returns videos for a user specific query.
            For example: Videos with actors born before 1970.

        Returns
        ----------
        List
            Returns a list of the videos in which a entity occurs. Format: [[<link>, <title>, <entity>], ...]
        """
        query = '''
        select distinct ?title ?link ?entity 
        where { 
            ?scene a video:Scene; 
                foaf:depicts ?entity; 
                video:sceneFrom ?video. 
            ?video dc:identifier ?link;
                    dc:title ?title.
            
            service <http://dbpedia.org/sparql> { 
                ?entity dbo:birthDate ?date 
            } 
            
            filter (?date < "19700101"^^xsd:date) 
        }
        '''
        return self.store.query(query)
