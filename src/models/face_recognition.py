import os
import pickle
import logging
import numpy as np
import cv2
from deepface import DeepFace
from deepface.commons import functions
from mtcnn import MTCNN
from src.preprocessing.facial_preprocessing import face_alignment
from src.utils.utils import image_files_in_folder

LOGGER = logging.getLogger(__name__)


class FaceRecognition(object):
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

    def __init__(self, thumbnail_list: list = None,
                 thumbnails_path='data/thumbnails/',
                 # detector_name='mtcnn',
                 img_width=500,
                 align=True,  # for test performance improvement
                 distance_threshold=0.6,  # TODO(honglin): tune later
                 encoder_name='Dlib',
                 labels_path=None,
                 embeddings_path=None):
        """ create or load kg_encodings. create detector, encoder """
        self.thumbnail_list = thumbnail_list
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

    def represent(self, img, one_face=False, return_face_number=False):
        """ create embedings from img
        Params:
          img: img object | img_path
          one_face: can be True, for func create_embeddings()
          return_face_number: for distance tuning
        Returens:
          embeddings: list of face embeddings OR
          face_number: if return_face_number & face_number>1
        """
        embeddings = []

        if isinstance(img, str):  # img is a path
            img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)

        faces = self.detector.detect_faces(img)

        face_number = len(faces)

        if return_face_number and face_number != 1:  # for tuning distance threshold
          return face_number

        # get biggest face from thumbnails
        if one_face and face_number > 1:
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
            detected_face = face_alignment(img, self.target, face['keypoints'], align=self.align)

            embedding = self.encoder.predict(detected_face)[0]
            embeddings.append(embedding)

        return embeddings

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

        if self.thumbnail_list is not None:
            entity_dir_list = self.thumbnail_list

        for entity_dir in entity_dir_list:  # for every celebrity: format of dir: ID_Name entity_id, entity_name = entity_dir.split('_')
            entity_path = os.path.join(self.thumbnails_path, entity_dir)

            if not os.path.isdir(entity_path):
                continue

            for img_path in image_files_in_folder(
                    entity_path):  # for every img of celebrity, exactly one face in one pic
                LOGGER.info(f'Encoding {entity_dir}, thumbnail: {img_path}')
                entity_embedding = self.represent(img_path, one_face=True)

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
        unknown_img_embeddings = self.represent(unknown_img)

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
                    detected_faces.append('unknown')
                    # if not isinstance(unknown_img, str):
                    # display(Image.fromarray(unknown_img))

            else:  # build different standard ML model on top of embeddings
                if not recognizer_model.fitted:
                    recognizer_model.fit(embeddings=self.embeddings, labels=self.labels)
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
        fps = video.get(cv2.CAP_PROP_FPS)
        timestamps = [0.0]

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
                r = self.img_width / w
                dsize = (self.img_width, int(h * r))
                frame = cv2.resize(frame, dsize)

            detected_faces = self.recognize_image(frame, recognizer_model)
            frame_faces_list.append(detected_faces)

            timestamps.append(timestamps[-1] + 1000 / fps)

            # frames.append(frame)
            # if len(frames) == batch_size:
            #  frame_faces_list.extend(self._batch_recognize_images(frames, recognizer_model))
            #  frames.clear()

        detected_faces = {entity for l in frame_faces_list for entity in l}

        return detected_faces, frame_faces_list, timestamps[1:]

