import os
import face_recognition
from face_recognition.face_recognition_cli import image_files_in_folder
import cv2
import numpy as np
import pandas as pd
import pickle
import heapq
from PIL import Image
import logging
# import openface
# import openface.openface.align_dlib as openface
# import dlib

LOGGER = logging.getLogger(__name__)


class FaceHunter():
    """recognize faces in videos

    Parameters:
      thumbnails_path
      detector_model: default cnn, can be hog
      img_width: scale the image to fixed new width
      distance_threshold

    Attributes:
      labels_path
      embeddings_path
      embeddings: list of entity embeddings
      labels: list of entity names
    """

    def __init__(self, thumbnails_path='data/thumbnails/',
                 detector_model='cnn',
                 img_width=500,
                 distance_threshold=0.6):
        """ create or load kg_encodings """
        self.thumbnails_path = thumbnails_path
        self.detector_model = detector_model
        self.img_width = img_width
        self.distance_threshold = distance_threshold
        self.labels_path = 'data/embeddings/labels.pickle'
        self.embeddings_path = 'data/embeddings/embeddings.pickle'
        self.labels, self.embeddings = self.load_embeddings()  # store the 2 lists in labels.pickle encoddings.pickle
        # self.face_detector = dlib.get_frontal_face_detector()
        # self.predictor_model = 'openface/models/dlib/shape_predictor_68_face_landmarks.dat'
        # self.face_pose_predictor = dlib.shape_predictor(self.predictor_model)
        # self.face_aligner = openface.AlignDlib(self.predictor_model)

    def _get_img_embeddings(self, img, locations=None, one_face=False):
        """ create embeddings from img

        Params:
          img: img object | img_path
          locations: support batch
          one_face: can be True, for func create_embeddings()
        Returens:
          embeddings: list of face embeddings
        """
        embeddings = []
        if isinstance(img, str):  # img is a path
            img = face_recognition.load_image_file(img)

        if locations is None:
            locations = face_recognition.face_locations(img, model=self.detector_model)

        if len(locations) == 0:
            return embeddings

        if one_face and len(locations) > 1:
            LOGGER.warning('there are more than 1 face in the img.')
            return embeddings

        embeddings = face_recognition.face_encodings(img, locations)  # if no alignment

        """ later with face alignment
        for location locations:
          # TODO(honglin): face alignment
          face_embedding = face_recognition.face_encodings(img, location)
          embeddings.append(face_embedding[0])
        """
        """face alignment
          top, right, bottom, left = location
          display(Image.fromarray(unknown_img[top:bottom, left:right]))
          print(len(self.face_detector(unknown_img, 1)))
          detected_face = self.face_detector(unknown_img, 1)[i]
          pose_landmarks = self.face_pose_predictor(unknown_img, detected_face)
          alignedFace = self.face_aligner.align(300, unknown_img, detected_face, landmarkIndices=openface.AlignDlib.INNER_EYES_AND_BOTTOM_LIP)
          display(Image.fromarray(alignedFace))
        """
        return embeddings

    def create_embeddings(self):
        """ create and save face embeddings and entity labels of thumbnails in KnowledgeGraph

        Returns:
          embeddings: list of face embeddings
          labels: list of entity names [ID_NAME,...]
        """
        # TODO(honglin): LabelEncoder
        entity_dir_list = os.listdir(self.thumbnails_path)
        embeddings = []
        labels = []

        for entity_dir in entity_dir_list:  # for every celebrity: format of dir: ID_Name entity_id, entity_name = entity_dir.split('_')
            entity_path = os.path.join(self.thumbnails_path, entity_dir)

            if not os.path.isdir(entity_path):
                continue

            for img_path in image_files_in_folder(
                    entity_path):  # for every img of celebrity, exactly one face in one pic
                LOGGER.info(f'Encoding {entity_dir}, thumbnail: {img_path}')
                entity_embedding = self._get_img_embeddings(img_path)

                if not entity_embedding:
                    LOGGER.warning(f'Could not create encoding for image {img_path}')
                    continue

                embeddings.append(entity_embedding[0])
                labels.append(entity_dir)

        # write to disk
        with open(self.labels_path, 'wb') as f:
            f.write(pickle.dumps(labels))
        with open(self.embeddings_path, 'wb') as f:
            f.write(pickle.dumps(embeddings))
        return labels, embeddings

    def load_embeddings(self):
        if os.path.exists(self.labels_path) and os.path.exists(self.embeddings_path):
            labels = pickle.loads(open(self.labels_path, "rb").read())
            embeddings = pickle.loads(open(self.embeddings_path, "rb").read())
            return labels, embeddings
        return self.create_embeddings()

    def recognize_image(self, unknown_img, recognizer_model=None, locations=None):
        """ recognize faces in image

        Params:
          unknown_img: image_path or image object(frame)
          recognizer_model: standard ML classifier

        Results:
          detected_faces: list of detected entity names in unknown_img
        """
        detected_faces = []
        unknown_img_embeddings = self._get_img_embeddings(unknown_img, locations)
        if not unknown_img_embeddings:
            return detected_faces  # return []

        for unknown_img_embedding in unknown_img_embeddings:  # for each face in the image
            if not recognizer_model:  # run basic recognition
                face_distances = face_recognition.face_distance(self.embeddings, unknown_img_embedding)
                min_distance = np.min(face_distances)

                if min_distance < self.distance_threshold:
                    entity = self.labels[np.argmin(face_distances)]
                    detected_faces.append(entity)

                else:  # TODO(honglin): delete after testing
                    LOGGER.info('face detected but no match in the below image')
                    if not isinstance(unknown_img, str):
                        display(Image.fromarray(unknown_img))

            else:  # build different standard ML model on top of embeddings
                entity = recognizer_model.predict(unknown_img_embeddings)
                if entity:
                    detected_faces.append(entity)

        return detected_faces

    def _batch_recognize_images(self, frames, recognizer_model):
        frame_faces_list = []
        batch_of_face_locations = face_recognition.batch_face_locations(frames, batch_size=len(frames))
        for frame, locations in zip(frames, batch_of_face_locations):
            if not locations:  # TODO(honglin):delete after testing
                LOGGER.info('no faces detected in the below image')
                display(Image.fromarray(frame))
            detected_faces = self.recognize_image(frame, recognizer_model, locations)
            frame_faces_list.append(detected_faces)
        return frame_faces_list  # nested list

    def recognize_video(self, video_path, recognizer_model=None):
        """ recognize faces by frame

        Params:
          video_path

        Returns:
          frame_faces_list: list of list [[entity1, entity2], [], [entity1]]
          detected_faces: list of identical entities
        """
        LOGGER.info(f'Starting face recognition on {video_path}')

        video = cv2.VideoCapture(video_path)

        frame_faces_list = []
        frames = []
        batch_size = 128

        while video.isOpened():
            success, frame = video.read()

            if not success:
                if len(frames) > 0:
                    frame_faces_list.extend(self._batch_recognize_images(frames, recognizer_model))
                    frames.clear()
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # scale the frame
            w, h = frame.shape[1], frame.shape[0]
            if w > self.img_width:
                r = img_width / w
                dsize = (img_width, int(h * r))
                frame = cv2.resize(frame, dsize)

            frames.append(frame)

            if len(frames) == batch_size:
                frame_faces_list.extend(self._batch_recognize_images(frames, recognizer_model))
                frames.clear()

        detected_faces = {entity for l in frame_faces_list for entity in l}

        return frame_faces_list, detected_faces

    def recognize_videos(self, dir_path='videos/ytcelebrity/', recognizer_model=None):  # haven't run and test
        """recognize all the videos in one dir

        Params:

        Returns:
          predicted: list of dict {video | frame_faces | faces}

        """
        predicted = []
        video_paths = []

        if os.path.exists(os.path.join(dir_path, 'information.csv')):  # have't run
            info = pd.read_csv(os.path.join(dir_path, 'information.csv'))
            info['path'] = info['file'].apply(lambda x: os.path.join(dir_path, x))
            video_paths = info['path'].tolist()
        else:
            video_paths = os.listdir(dir_path)

        LOGGER.info(f'there are {len(video_paths)} in the directory')

        for video_path in video_paths:
            LOGGER.info(f'recognizing the video: {video_path}')
            frame_faces_list, detected_faces = self.recognize_video(os.path.join(dir_path, video_path),
                                                                    recognizer_model)
            predicted.append({'video': video_path, 'frame_faces': frame_faces_list, 'faces': detected_faces})
        return predicted

