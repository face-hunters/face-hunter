import os
import tempfile
from src.knowledge_graph.graph import Graph
from src.data.youtube import download_youtube_video
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from src.models.face_recognition import FaceRecognition
from src.postprocessing.graph_postprocessing import extract_scenes


class FlaskApi(object):
    """ API for flask website view functions 
    
    Attribute：
      recognizer_model: ANN
      face_recognition: FaceRecognition
      graph: Knowledge Graph

    """

    def __init__(self,
                 # parameters for Graph
                 storage_type: str = 'memory',
                 memory_path: str = 'models/store',
                 virtuoso_url: str = None,
                 virtuoso_graph: str = None,
                 virtuoso_username: str = None,
                 virtuoso_password: str = None,
                 dbpedia_csv: str = '../data/thumbnails/dbpedia_thumbnails/Thumbnails_links.csv',
                 wikidata_csv: str = '../data/thumbnails/wikidata_thumbnails/Thumbnails_links.csv',
                 # parameters for FaceRecognition
                 thumbnail_list: list = None,
                 thumbnails_path='../data/thumbnails/thumbnails',
                 img_width=500,
                 distance_threshold=0.4,
                 encoder_name='Facenet',
                 labels_path='../data/embeddings/labels_facenet.pickle',
                 embeddings_path='../data/embeddings/embeddings_facenet.pickle',
                 index_path='../data/embeddings/index.bin'):
        """ Instantiate ApproximateKNearestNeighbors， FaceRecognition and Graph """
        self.recognizer_model = ApproximateKNearestNeighbors(distance_threshold=distance_threshold,
                                                             index_path=index_path)
        self.face_recognition = FaceRecognition(thumbnail_list, thumbnails_path, img_width,
                                                encoder_name, labels_path, embeddings_path)
        self.graph = Graph(storage_type, memory_path, virtuoso_url, virtuoso_graph, virtuoso_username,
                           virtuoso_password, dbpedia_csv, wikidata_csv)

    def recognize_local_video(self, path):
        return self.face_recognition.recognize_video(path, self.recognizer_model)

    def recognize_youtube_video(self, identifier, by='frame', frame_threshold=7):
        """
        if video is in KG, query from KG
        if not, download and recognize video, then insert video to KG

        Parameters
        ----------
        identifier: youtube video id
        by: recognize by 'frame' or 'second'

        Returns
        ----------
        result: [[entity, start, end],...]
      """
        result = []
        if self.graph.video_exists(identifier):
            result = [scene[1:] for scene in
                      self.graph.get_scenes_from_video(identifier)]  # [scene, entity, start, end]
            return result

        path_to_video = download_youtube_video(f'https://www.youtube.com/watch?v={identifier}', tempfile.gettempdir())

        recognized_entities, frame_wise_entities, timestamps = self.face_recognition.recognize_video(path_to_video,
                                                                                                     self.recognizer_model,
                                                                                                     by)

        self.graph.insert_video(identifier, os.path.split(path_to_video)[1])
        scenes = extract_scenes(frame_wise_entities, timestamps, frame_threshold)
        for scene in scenes:
            result.append([scene.names[0].tolist(), str(scene.start[0]).split('.')[0],
                           str(scene.end[0]).split('.')[0]])  # accurate to second
            self.graph.insert_scene(scene.names[0], identifier, scene.start[0], scene.end[0])

        return result

    def get_videos_by_sparql(self, query, filters):
        return self.graph.get_videos_with_filters(query, filters)

    def get_videos_by_entity(self, entity):
        return self.graph.get_scenes_with_entity(entity)
