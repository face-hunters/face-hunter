import os
import tempfile
from src.knowledge_graph.graph import Graph
from src.data.youtube import download_youtube_video
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from src.models.face_recognition import FaceRecognition
from src.postprocessing.graph_postprocessing import extract_scenes


class Hunter(object):
    """ Class to use the entity linking in other projects and on the website. """

    def __init__(self, url: str = None):
        """
        Args:
            url (str): URL of the video on YouTube.
        """
        self.url = url
        self.identifier = self.url.split('=')[1]
        self.path_to_video = None
        self.face_detection = None

    def fit(self,
            thumbnail_list=None,
            thumbnails_path='data/thumbnails/thumbnails',
            img_width=500,
            encoder_name: str ='Dlib',
            labels_path='data/embeddings/labels.pickle',
            embeddings_path='data/embeddings/embeddings.pickle'
            ):
        """ Creates the embeddings for a dictionary of thumbnails.

        Args:
            thumbnail_list (list): list of thumbnails to load.
            thumbnails_path (str): Path to the directory containing the thumbnails.
            img_width (int): Size to which the thumbnails should be resized.
            encoder_name (str): Specifies the method to create embeddings of faces in an image.
            labels_path (str): Path where the label-information should be saved.
            embeddings_path (str): Path where the embeddings should be saved.

        Returns:
            self
        """
        self.face_detection = FaceRecognition(
            thumbnail_list,
            thumbnails_path,
            img_width,
            encoder_name,
            labels_path,
            embeddings_path
        )
        return self

    def recognize(self,
                  algorithm='appr',
                  method='hnsw',
                  space='cosinesimil',
                  distance_threshold=0.4,
                  index_path='data/embeddings/index.bin',
                  k=1,
                  recognize_by: str = 'second'
                  ) -> list:
        """ Get a list of entities that could be recognized in the video.

        Args:
            algorithm (str): Algorithm to use for the similarity-calculation. Should be '1nn' for 1-Nearest Neighbors with euclidean distance, 'appr' for approximate k-Nearest Neighbors.
            distance_threshold (float): The threshold above which faces are recognized as being similar.
            method (str): Type of graph to use for the k-nearest neighbor approximation. See https://github.com/nmslib/nmslib/blob/master/manual/methods.md for available options. Only necessary if algorithm = 'appr'.
            space (str): Similarity measure to use in the space. Only necessary if algorithm = 'appr'.
            index_path (str): Path to an existing nmslib-index. Only necessary if algorithm = 'appr'.
            k (int): The number of k-nearest neighbors to consider for the detection. Only necessary if algorithm = 'appr'.
            recognize_by (str): Recognize by 'second' or 'frame'.

        Returns:
            entities (list): Entities found in the video.
        """
        if algorithm == 'appr':
            detector = ApproximateKNearestNeighbors(method,
                                                    space,
                                                    distance_threshold,
                                                    index_path,
                                                    k)
        elif algorithm == '1nn':
            detector = None
        else:
            raise Exception('Unknown Predictor')

        self.path_to_video = download_youtube_video(self.url, tempfile.gettempdir())
        return self.face_detection.recognize_video(self.path_to_video, detector, distance_threshold, recognize_by)

    def link(self,
             storage_type: str = 'memory',
             algorithm='appr',
             method='hnsw',
             space='cosinesimil',
             distance_threshold=0.4,
             index_path='data/embeddings/index.bin',
             k=1,
             recognize_by: str = 'second',
             memory_path: str = 'models/store',
             virtuoso_url: str = None,
             virtuoso_graph: str = None,
             virtuoso_username: str = None,
             virtuoso_password: str = None,
             dbpedia_csv: str = 'data/thumbnails/dbpedia_thumbnails/Thumbnails_links.csv',
             wikidata_csv: str = 'data/thumbnails/wikidata_thumbnails/Thumbnails_links.csv'):
        """ Recognize entities in a video and add corresponding links to the knowledge graph.

        Args:
            algorithm (str): Algorithm to use for the similarity-calculation. Should be '1nn' for 1-Nearest Neighbors with euclidean distance, 'appr' for approximate k-Nearest Neighbors.
            distance_threshold (float): The threshold above which faces are recognized as being similar.
            method (str): Type of graph to use for the k-nearest neighbor approximation. See https://github.com/nmslib/nmslib/blob/master/manual/methods.md for available options. Only necessary if algorithm = 'appr'.
            space (str): Similarity measure to use in the space. Only necessary if algorithm = 'appr'.
            index_path (str): Path to an existing nmslib-index. Only necessary if algorithm = 'appr'.
            k (int): The number of k-nearest neighbors to consider for the detection. Only necessary if algorithm = 'appr'.
            recognize_by (str): Recognize by 'second' or 'frame'.
            storage_type (str): Whether to save links to a local rdf-file or a Virtuoso database. Should be 'memory' for a local file,
                            'virtuoso' for Virtuoso.
            memory_path (str): Path to which the links should be written. Only necessary if storage_type = memory.
            virtuoso_url (str): URL of the Virtuoso-SPARQL-instance. Only necessary if storage_type = virtuoso.
            virtuoso_graph (str): URL of the Virtuoso-Graph in which the links should be saved. Only necessary if storage_type = virtuoso.
            virtuoso_username (str): Username to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            virtuoso_password (str): Password to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            dbpedia_csv (str): Path of the normalized DBpedia-thumbnail-information.
            wikidata_csv (str): Path of the normalized Wikidata-thumbnail-information.

        Returns:
            new_links (bool): Whether the video already existed in the database or not.
        """
        graph = Graph(storage_type,
                      memory_path,
                      virtuoso_url,
                      virtuoso_graph,
                      virtuoso_username,
                      virtuoso_password,
                      dbpedia_csv,
                      wikidata_csv)

        if not graph.video_exists(self.identifier):
            recognized_entities, frame_wise_entities, timestamps = self.recognize(algorithm, method, space,
                                                                                  distance_threshold, index_path, k,
                                                                                  recognize_by)

            graph.insert_video(self.identifier, os.path.split(self.path_to_video)[1])
            scenes = extract_scenes(frame_wise_entities, timestamps, 3)
            for scene in scenes:
                graph.insert_scene(scene.names[0], self.identifier, scene.start[0], scene.end[0])
            return True
        return False

    @staticmethod
    def search(entity: str = None,
               storage_type: str = 'memory',
               memory_path: str = 'models/store',
               virtuoso_url: str = None,
               virtuoso_graph: str = None,
               virtuoso_username: str = None,
               virtuoso_password: str = None,
               dbpedia_csv: str = None,
               wikidata_csv: str = None):
        """ Allows to search for scenes in a knowledge graph using the entity name.

        Args:
            entity (str): Name of the entity to search for. Should be the label, DBpedia- or Wikidata-URI.
            storage_type (str): Whether to save links to a local rdf-file or a Virtuoso database. Should be 'memory' for a local file,
                            'virtuoso' for Virtuoso.
            memory_path (str): Path to which the links should be written. Only necessary if storage_type = memory.
            virtuoso_url (str): URL of the Virtuoso-SPARQL-instance. Only necessary if storage_type = virtuoso.
            virtuoso_graph (str): URL of the Virtuoso-Graph in which the links should be saved. Only necessary if storage_type = virtuoso.
            virtuoso_username (str): Username to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            virtuoso_password (str): Password to access the Virtuoso instance. Only necessary if storage_type = virtuoso.
            dbpedia_csv (str): Path of the normalized DBpedia-thumbnail-information.
            wikidata_csv (str): Path of the normalized Wikidata-thumbnail-information

        Returns:
            scenes (list): The scenes in which the entity occurs.
        """
        return Graph(storage_type,
                     memory_path,
                     virtuoso_url,
                     virtuoso_graph,
                     virtuoso_username,
                     virtuoso_password,
                     dbpedia_csv,
                     wikidata_csv).get_scenes_with_entity(entity)
