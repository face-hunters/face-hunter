import logging
from datetime import timedelta
from rdflib import URIRef, Literal
from rdflib.namespace import DC, RDF, Namespace, FOAF, XSD
import pandas as pd
from src.knowledge_graph.memory_store import MemoryStore
from src.knowledge_graph.virtuoso_store import VirtuosoStore
from src.utils.utils import get_config
from src.data.knowledge_graphs import get_same_as_link, get_uri_from_label, get_uri_from_csv
import os

on_rtd = os.environ.get('READTHEDOCS') == 'True'
on_flask = os.environ.get('FLASK_running') == 'True'

LOGGER = logging.getLogger('graph')

if on_rtd or on_flask:
    CONFIG = get_config('../src/utils/config.yaml')
else:
    CONFIG = get_config('src/utils/config.yaml')

HOME_URI = CONFIG['rdf']['uri']

MPEG7 = Namespace('http://purl.org/ontology/mpeg7/')
VIDEO = Namespace('http://purl.org/ontology/video/')
TEMPORAL = Namespace('http://swrl.stanford.edu/ontologies/builtins/3.3/temporal.owl')
DBO = Namespace('http://dbpedia.org/ontology/')
DBR = Namespace('http://dbpedia.org/resource/')


class Graph(object):
    """ Links new videos with their entities in a knowledge graph and allows to look up user queries. """

    def __init__(self,
                 storage_type: str = 'memory',
                 memory_path: str = 'models/store',
                 virtuoso_url: str = None,
                 virtuoso_graph: str = None,
                 virtuoso_username: str = None,
                 virtuoso_password: str = None,
                 dbpedia_csv: str = None,
                 wikidata_csv: str = None):
        """
        Args:
            storage_type (str): Whether to save links to a local rdf-file or a Virtuoso database. Should be 'memory' for a local file, 'virtuoso' for Virtuoso.
            memory_path (str): Path to which the links should be written. Only necessary if storage_type = memory.
            virtuoso_url (str): URL of the Virtuoso-SPARQL-instance. Only necessary if storage_type = virtuoso.
            virtuoso_graph (str): URL of the Virtuoso-Graph in which the links should be saved. Only necessary if storage_type = virtuoso.
            virtuoso_username (str): Username to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            virtuoso_password (str): Password to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            dbpedia_csv (str): Path of the normalized DBpedia-thumbnail-information.
            wikidata_csv (str): Path of the normalized Wikidata-thumbnail-information
        """
        self.storage_type = storage_type
        if storage_type == 'memory':
            self.store = MemoryStore(memory_path)
        elif storage_type == 'virtuoso':
            self.store = VirtuosoStore(virtuoso_url, virtuoso_graph, virtuoso_username, virtuoso_password)
        else:
            raise Exception('Unknown storage type')

        self.entity_data = None
        if dbpedia_csv is not None and wikidata_csv is not None:
            self.entity_data = pd.concat([pd.read_csv(dbpedia_csv), pd.read_csv(wikidata_csv)])
        elif  wikidata_csv is not None:
            self.entity_data = pd.read_csv(wikidata_csv)
        elif dbpedia_csv is not None:
            self.entity_data = pd.read_csv(dbpedia_csv)

    def insert_video(self, youtube_id: str, title: str):
        """ Creates the rdf triples for a new video.

        Args:
            youtube_id (str): Id of a youtube video to be linked. For example a4T5ylNQk6g for https://www.youtube.com/watch?v=a4T5ylNQk6g.
            title (str): The title of the video.
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')

        self.store.insert((video_uri, RDF['type'], MPEG7['Video']))
        self.store.insert((video_uri, DC['identifier'], Literal(f'http://www.youtube.com/watch?v={youtube_id}')))
        self.store.insert((video_uri, DC['title'], Literal('.'.join(title.split('.')[:-1]))))
        self.store.commit()

    def insert_scene(self, entities: list, youtube_id: str, start_time: timedelta, end_time: timedelta):
        """ Creates the link between an entity and a video from youtube.

        Args:
            entities (list): Names of the occurring entities.
            youtube_id (str): Id of a youtube video to be linked. For example a4T5ylNQk6g for https://www.youtube.com/watch?v=a4T5ylNQk6g.
            start_time (timedelta): Start time of the scene in the respective video.
            end_time (timedelta): End time of the scene in the respective video.
        """
        video_uri = URIRef(f'{HOME_URI}{youtube_id}')
        scene_uri = URIRef(f'{HOME_URI}{youtube_id}#t={str(start_time).split(".", 2)[0]},{str(end_time).split(".", 2)[0]}')

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
            if self.entity_data is None:
                dbpedia_uri, wikidata_uri = get_uri_from_label(entity)
            else:
                dbpedia_uri, wikidata_uri = get_uri_from_csv(entity, self.entity_data)
            if dbpedia_uri is not None:
                self.store.insert((scene_uri, FOAF['depicts'], URIRef(dbpedia_uri)))
            elif wikidata_uri is not None:
                self.store.insert((scene_uri, FOAF['depicts'], URIRef(wikidata_uri)))
            else:
                LOGGER.info(f'Failed to create link to {entity} for video {youtube_id}')
        self.store.commit()

    def video_exists(self, youtube_id: str) -> bool:
        """ Returns whether a video is already in the graph or not

        Args:
            youtube_id (str): Id of the YouTube-Video.

        Returns:
            exists (bool): Whether it exists or not.
        """
        return self.store.exists(youtube_id)

    def get_scenes_from_video(self, identifier: str):
        """ Returns all scenes for a video

        Args:
            identifier (str): Identifier of the video on YouTube

        Returns:
            scenes (list): Returns a list of the scenes with a scene_uri, entity, start and end
        """
        query = ('SELECT ?scene ?entity ?start ?end'
                 ' WHERE {'
                 ' ?scene a video:Scene ;'
                 f' video:sceneFrom <{HOME_URI + identifier}>;'
                 ' foaf:depicts ?entity;'
                 ' temporal:hasStartTime ?start;'
                 ' temporal:hasFinishTime ?end.'
                 '}')
        print(query)
        return self.store.query(query)

    def get_scenes_with_entity(self, identifier: str):
        """ Returns all scenes for an entity

        Args:
            identifier (str): Can be the name of the entity or a dbpedia/wikidata link.

        Returns:
            scenes (list): Returns a list of the videos in which a entity occurs. Format: [[<link>, <title>], ...]
        """

        if identifier.startswith('http://www.wikidata'):
            identifier = get_same_as_link(identifier)
        elif not identifier.startswith('http://dbpedia'):
            if self.entity_data is None:
                uris = get_uri_from_label(identifier)
            else:
                uris = get_uri_from_csv(identifier, self.entity_data)
            identifier = uris[0] if uris[0] is not None else uris[1]
            if identifier is None:
                LOGGER.warning('Could not identify entity using the label')
                return None

        query = ('SELECT  distinct ?title ?link ?dbpedia_entity ?start ?end'
                 ' WHERE {'
                 ' ?scene a video:Scene ;'
                 f' foaf:depicts <{identifier}> ;'
                 f' foaf:depicts ?dbpedia_entity ;'
                 ' temporal:hasStartTime ?start ;'
                 ' temporal:hasFinishTime ?end ;' 
                 ' video:sceneFrom ?video .'
                 ' ?video a mpeg7:Video ;'
                 ' dc:identifier ?link ;'
                 ' dc:title ?title .'
                 ' }')
        return self.store.query(query)

    def get_videos_with_filters(self, query: str, filters: str):
        """ Returns videos for a user specific query.

            Example:
            select distinct ?title ?link ?dbpedia_entity
            where {
            ?scene a video:Scene;
            foaf:depicts ?dbpedia_entity;
            video:sceneFrom ?video.
            ?video dc:identifier ?link;
            dc:title ?title.

            service <http://dbpedia.org/sparql> {
            ?dbpedia_entity dbo:birthDate ?date;
            owl:sameAs ?wikidata_entity
            }

            service <https://query.wikidata.org/sparql> {
            ?wikidata_entity <http://www.wikidata.org/prop/direct/P21> ?sex .
            ?sex rdfs:label ?sex_label
            }

            filter (regex(str(?wikidata_entity), "www.wikidata.org") && (?sex_label = "male"@en) && ?date < "19700101"^^xsd:date)
            }

        Args:
            query (str): Further query details which are being inserted into the main query.
            filters (str): Allows the specification of filters to apply in the query.

        Returns:
            scenes (list): Returns a list of the scenes in which a entity occurs. Format: [[<title>, <link>, <dbpedia_entity>, <start>, <end>], ...]
        """
        query = (
            'select distinct ?title ?link ?dbpedia_entity ?start ?end'
            ' where { '
            ' ?scene a video:Scene; '
            ' foaf:depicts ?dbpedia_entity;'
            ' temporal:hasStartTime ?start;'
            ' temporal:hasFinishTime ?end;'
            ' video:sceneFrom ?video. '
            ' ?video dc:identifier ?link;'
            ' dc:title ?title.'
            f' {query}'
            f' {"filter ( "+filters+" )" if filters is not None else ""}'
            ' }'
        )
        return self.store.query(query)
