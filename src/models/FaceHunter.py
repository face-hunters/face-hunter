import os
import re
import pickle
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import cv2
from deepface import DeepFace
from deepface.detectors import FaceDetector
from deepface.commons import functions
from mtcnn import MTCNN
from keras.preprocessing.image import img_to_array

LOGGER = logging.getLogger(__name__)


class FaceHunter():
    """recognize faces in videos

    Parameters:
      thumbnails_path
      #detector_model: default cnn, can be hog
      img_width: scale the image to fixed new width
      align: whether apply face alignment
      distance_threshold
      encoder_name: "VGG-Face", "Facenet", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib"
      #detector_name: 'opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface'
      labels_path
      embeddings_path

    Attributes:
      embeddings: list of entity embeddings
      labels: list of entity names
      detector: face detector model MTCNN https://github.com/ipazc/mtcnn
      encoder: face embedding encoder
      target: encoder input layer image shape (w,h)
    """

    def __init__(self, thumbnails_path='data/thumbnails/',
                 # detector_name='mtcnn',
                 img_width=500,
                 align=True,  # for test performance improvement
                 distance_threshold=0.6,  # TODO(honglin): tune later
                 encoder_name='Dlib',
                 labels_path='data/embeddings/labels.pickle',
                 embeddings_path='data/embeddings/embeddings.pickle'):
        """ create or load kg_encodings. create detector, encoder """
        self.thumbnails_path = thumbnails_path
        self.img_width = img_width
        self.align = align
        self.distance_threshold = distance_threshold
        self.labels_path = labels_path
        self.embeddings_path = embeddings_path
        self.detector = MTCNN()
        # self.detector = FaceDetector.build_model(detector_name)
        self.encoder = DeepFace.build_model(encoder_name)
        self.target = functions.find_input_shape(self.encoder)  # (150,150) encoder input shape
        self.labels, self.embeddings = self.load_embeddings()  # store the 2 lists in labels.pickle encoddings.pickle

    def face_alignment(self, img, keypoints, blank=0.3, align=True):  # TODO(honglin):delete align parameters later
        left_eye = keypoints['left_eye']
        right_eye = keypoints['right_eye']
        mouth_left = keypoints['mouth_left']
        mouth_right = keypoints['mouth_right']

        eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
        mouth_center = ((mouth_left[0] + mouth_right[0]) // 2, (mouth_left[1] + mouth_right[1]) // 2)

        # get rotation angle
        dY = right_eye[1] - left_eye[1]
        dX = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dY, dX))

        # get scale by the distance from eye center to mouth center
        desiredDist = (1 - 2 * blank) * self.target[1]
        dY = mouth_center[1] - eye_center[1]
        dX = mouth_center[0] - eye_center[0]
        dist = np.sqrt((dX ** 2) + (dY ** 2))
        scale = desiredDist / dist

        M = cv2.getRotationMatrix2D(eye_center, angle, scale)

        # TODO(honglin): performance comparision use , delete later
        if not align:
            M = cv2.getRotationMatrix2D(keypoints['nose'], 0, scale)

        # translation
        tX = self.target[0] * 0.5
        tY = self.target[1] * blank
        M[0, 2] += (tX - eye_center[0])
        M[1, 2] += (tY - eye_center[1])

        aligned_face = cv2.warpAffine(img, M, self.target, flags=cv2.INTER_CUBIC)

        # TODO(honglin):face alignment test use, delete later
        # plt.imshow(aligned_face)
        # plt.show()

        # input layer shape
        img_pixels = img_to_array(aligned_face)
        img_pixels = np.expand_dims(aligned_face, axis=0)
        img_pixels = img_pixels / 255

        return img_pixels

    def _get_img_embeddings(self, img, one_face=False):
        """ create embedings from img

        Params:
          img: img object | img_path
          one_face: can be True, for func create_embeddings()
        Returens:
          embeddings: list of face embeddings
        """
        embeddings = []

        if isinstance(img, str):  # img is a path
            img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)

        faces = self.detector.detect_faces(img)

        # get biggest face from thumbnails
        if one_face and len(faces) > 1:
            height = [face['box'][3] for face in faces]  # box: [x, y, w, h]
            index = height.index(max(height))
            faces = [faces[index]]

        for face in faces:
            x, y, w, h = face['box']
            detected_face = img[int(y):int(y + h), int(x):int(x + w)]

            # TODO(honglin): face alignment test use, delete later
            # print('original face')
            # plt.imshow(detected_face)
            # plt.show()

            # aligned_face = FaceDetector.alignment_procedure(detected_face, left_eye, right_eye)
            detected_face = self.face_alignment(img, face['keypoints'], align=self.align)

            embedding = self.encoder.predict(detected_face)[0]
            embeddings.append(embedding)

        return embeddings

    # TODO(Honglin): move to Helper module
    def image_files_in_folder(self, folder):  # copy from face_recognition library
        return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

    def create_embeddings(self):
        """ create and save face embeddings and entity labels of thumbnails in KnowledgeGraph

        Returns:
          embeddings: list of face embeddings
          labels: list of entity names [ID_NAME,...]
        """
        # TODO: Big Data Solution
        entity_dir_list = os.listdir(self.thumbnails_path)
        embeddings = []
        labels = []

        for entity_dir in entity_dir_list:  # for every celebrity: format of dir: ID_Name entity_id, entity_name = entity_dir.split('_')
            entity_path = os.path.join(self.thumbnails_path, entity_dir)

            if not os.path.isdir(entity_path):
                continue

            for img_path in self.image_files_in_folder(
                    entity_path):  # for every img of celebrity, exactly one face in one pic
                LOGGER.info(f'Encoding {entity_dir}, thumbnail: {img_path}')
                entity_embedding = self._get_img_embeddings(img_path, one_face=True)

                if not entity_embedding:
                    LOGGER.warning(f'Could not create encoding for image {img_path}')
                    continue

                if len(entity_embedding) > 1:
                    LOGGER.warning(f'There are more than one faces in image {img_path}')
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

    def recognize_image(self, unknown_img, recognizer_model=None):
        """ recognize faces in image

        Params:
          unknown_img: image_path or image object(frame)
          recognizer_model: face recognition model  .   interface for build other models on the top of embeddings

        Results:
          detected_faces: list of detected entity names in unknown_img
        """
        detected_faces = []
        unknown_img_embeddings = self._get_img_embeddings(unknown_img)

        for unknown_img_embedding in unknown_img_embeddings:  # for each face in the image
            if not recognizer_model:  # run basic recognition
                # face_distances = face_recognition.face_distance(self.embeddings, unknown_img_embedding)
                a = np.matmul(self.embeddings, unknown_img_embedding)
                b = np.linalg.norm(self.embeddings, axis=1)
                c = np.linalg.norm(unknown_img_embedding)
                face_distances = 1 - a / (b * c)
                min_distance = np.min(face_distances)

                if min_distance < self.distance_threshold:
                    entity = self.labels[np.argmin(face_distances)]
                    detected_faces.append(entity)

                else:  # TODO(honglin): delete after testing
                    LOGGER.info('face detected but no match')
                    # if not isinstance(unknown_img, str):
                    # display(Image.fromarray(unknown_img))

            else:  # build different standard ML model on top of embeddings
                entity = recognizer_model.predict(unknown_img_embedding)
                if entity:
                    detected_faces.append(entity)

        return detected_faces

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
        # frames = []
        # batch_size = 128

        while video.isOpened():
            success, frame = video.read()

            if not success:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # scale the frame
            w, h = frame.shape[1], frame.shape[0]
            if w > self.img_width:
                r = img_width / w
                dsize = (img_width, int(h * r))
                frame = cv2.resize(frame, dsize)

            detected_faces = self.recognize_image(frame)
            frame_faces_list.append(detected_faces)

            # frames.append(frame)
            # if len(frames) == batch_size:
            #  frame_faces_list.extend(self._batch_recognize_images(frames, recognizer_model))
            #  frames.clear()

        detected_faces = {entity for l in frame_faces_list for entity in l}

        return detected_faces, frame_faces_list

