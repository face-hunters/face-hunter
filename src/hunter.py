import os
import tempfile
from knowledge_graph.graph import Graph
from data.youtube import download_youtube_video
from models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from models.face_recognition import FaceRecognition
from postprocessing.graph_postprocessing import extract_scenes


class Hunter(object):

    def __init__(self, url: str = None):
        self.url = url
        self.identifier = self.url.split('=')[1]
        self.path_to_video = None
        self.face_detection = FaceRecognition()

    def recognize(self, method: str = 'approximate_k_neighbors') -> list:
        if method == 'approximate_k_neighbors':
            detector = ApproximateKNearestNeighbors()
        else:
            raise Exception('Unknown Detector')

        self.path_to_video = download_youtube_video(self.url, tempfile.gettempdir())
        return self.face_detection.recognize_video(self.path_to_video, detector)

    def link(self,
             storage_type: str = 'memory',
             memory_path: str = 'models/store',
             virtuoso_url: str = None,
             virtuoso_graph: str = None,
             virtuoso_username: str = None,
             virtuoso_password: str = None):
        graph = Graph(storage_type,
                      memory_path,
                      virtuoso_url,
                      virtuoso_graph,
                      virtuoso_username,
                      virtuoso_password)

        recognized_entities, frame_wise_entities, timestamps = self.recognize()
        if not graph.video_exists(self.identifier):
            graph.insert_video(self.identifier, os.path.split(self.path_to_video)[1])
            scenes = extract_scenes(frame_wise_entities, timestamps)
            for scene in scenes:
                graph.insert_scene(scene.names[0], self.identifier, scene.start[0], scene.end[0])

    @staticmethod
    def search(entity: str = None,
               storage_type: str = 'memory',
               memory_path: str = 'models/store',
               virtuoso_url: str = None,
               virtuoso_graph: str = None,
               virtuoso_username: str = None,
               virtuoso_password: str = None):
        return Graph(storage_type,
                     memory_path,
                     virtuoso_url,
                     virtuoso_graph,
                     virtuoso_username,
                     virtuoso_password).get_videos_with_entity_name(entity)
