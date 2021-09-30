import os
import pickle
import logging
import numpy as np
import cv2
from deepface import DeepFace
from deepface.commons import functions
from facenet_pytorch import MTCNN
from src.preprocessing.facial_preprocessing import face_alignment
from src.utils.utils import image_files_in_folder

LOGGER = logging.getLogger(__name__)


class FaceRecognition(object):
    """recognize faces in videos

    Parameters:
      thumbnails_list: for sample use
      thumbnails_path: path to thumbnail directory
      img_width: scale the image to fixed new width
      distance_threshold
      encoder_name: "VGG-Face", "Facenet", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib"
      labels_path: path to save and load thumbnail labels
      embeddings_path: path to save and load thumbnail embeddings

    Attributes:
      embeddings: list of entity embeddings
      labels: list of entity names
      detector: face detector model MTCNN https://github.com/ipazc/mtcnn
      encoder: face encoder(face recognition model)
      target: face recognition model's input layer image shape (w,h)
    """

    def __init__(self, thumbnail_list: list = None,
                 thumbnails_path='data/thumbnails/thumbnails',
                 img_width=500,
                 encoder_name='Dlib',
                 labels_path='data/embeddings/labels.pickle',
                 embeddings_path='data/embeddings/embeddings.pickle'):
        """ create or load kg_encodings. create detector, encoder """
        self.thumbnail_list = thumbnail_list
        self.thumbnails_path = thumbnails_path
        self.img_width = img_width
        self.labels_path = labels_path
        self.embeddings_path = embeddings_path
        self.detector = MTCNN(keep_all=True, post_process=False, device='cuda:0')
        self.encoder = DeepFace.build_model(encoder_name)
        self.target = functions.find_input_shape(self.encoder)  # (150,150) encoder input shape
        self.labels, self.embeddings = self.load_embeddings()  # store the 2 lists in labels.pickle encoddings.pickle

    def recognize_video(self, video_path, recognizer_model=None, distance_threshold=0.6, by='second'):
        """ recognize faces by frame
        Params:
          video_path
          recognizer_model: ANN
          by: recognize by 'second' or 'frame'
        Returns:
          frame_faces_list: list of list [[entity1, entity2], [], [entity1]]
          detected_faces: list of identical entities
          timestamps: [millisecond , ]
        """
        if not os.path.exists(video_path):
            LOGGER.info(f'{video_path} does not exists')

        LOGGER.info(f'Starting face recognition on {video_path}')

        video = cv2.VideoCapture(video_path)

        fps = video.get(cv2.CAP_PROP_FPS)
        frame_number = 0  # for recognize by second

        timestamps = []
        frame_faces_list = []

        # for batch processing
        frames = []
        batch_size = 128

        success, frame = video.read()

        while success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # scale the frame
            w, h = frame.shape[1], frame.shape[0]
            if w > self.img_width:
                r = self.img_width / w
                dsize = (self.img_width, int(h * r))
                frame = cv2.resize(frame, dsize)

            frames.append(frame)

            # batch detect
            if len(frames) == batch_size:
                frame_faces_list.extend(self.batch_recognize_images(frames, recognizer_model, distance_threshold))
                frames.clear()

            # detected_faces = self.recognize_image(frame, recognizer_model)
            # frame_faces_list.append(detected_faces)

            if by == 'frame':
                timestamp = (timestamps[-1] + 1000 / fps) if timestamps else 0.0
                timestamps.append(timestamp)

                success, frame = video.read()
            else:
                # by second
                timestamp = (timestamps[-1] + 1000) if timestamps else 0.0
                timestamps.append(timestamp)

                frame_number += fps
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                success, image = video.read()

        if len(frames) == 1:
            frame_faces_list.append(self.recognize_image(frames[0], recognizer_model))
        elif len(frames) > 1:
            frame_faces_list.extend(self.batch_recognize_images(frames, recognizer_model))
            frames.clear()

        detected_faces = {entity for l in frame_faces_list for entity in l}

        return detected_faces, frame_faces_list, timestamps

    def batch_recognize_images(self, unknown_imgs, recognizer_model=None, distance_threshold=0.6):
        detected_faces = []
        embeddings = self.batch_represent(unknown_imgs)

        # recognize img by frame
        for frame_embeddings in embeddings:
            detected_faces.append(self.recognize_image(frame_embeddings, recognizer_model, distance_threshold))

        return detected_faces

    def batch_represent(self, imgs):
        """ create embedings from img
        Params:
          imgs: list of frames

        Returens:
          embeddings: list of face embeddings
        """
        embeddings = []

        mtcnn_imput = [Image.fromarray(img) for img in imgs]

        boxes, confidence, keypoints = self.detector.detect(mtcnn_imput, landmarks=True)
        frames_faces_detection = []

        for i in range(len(boxes)):
            # there is face in the frame
            if boxes[i] is not None:
                frame_faces = [{
                    'box': [box[0], box[1], box[2] - box[0], box[3] - box[1]],
                    'confidence': confidence,
                    'keypoints': {
                        'left_eye': tuple(keypoints[0]),
                        'right_eye': tuple(keypoints[1]),
                        'nose': tuple(keypoints[2]),
                        'mouth_left': tuple(keypoints[3]),
                        'mouth_right': tuple(keypoints[4]),
                    }}
                    for box, confidence, keypoints in zip(boxes[i], confidence[i], keypoints[i])]

                frames_faces_detection.append(frame_faces)
            # there is no face in the frame
            else:
                frames_faces_detection.append([])

        aligned_faces = []
        for img, frame_faces in zip(imgs, frames_faces_detection):  # per frame, align face

            frame_aligned_faces = []

            for face in frame_faces:
                # align face
                aligned_face = face_alignment(img, self.target, face['keypoints'])
                frame_aligned_faces.append(aligned_face)

            aligned_faces.append(frame_aligned_faces)

        flat_aligned_faces = [face for l in aligned_faces for face in l]

        # batch encoding
        if len(flat_aligned_faces) > 1:  # otherwise, no face in the batch
            flat_aligned_faces = np.array(flat_aligned_faces)
            flat_embeddings = self.encoder.predict(flat_aligned_faces)

        count = 0
        for i in range(len(aligned_faces)):
            frame_embeddings = []
            for j in range(len(aligned_faces[i])):
                frame_embeddings.append(flat_embeddings[count])
                count += 1
            embeddings.append(frame_embeddings)

        return embeddings

    def create_embeddings(self):
        """ create and save face embeddings and entity labels of thumbnails in KnowledgeGraph
        Returns:
          embeddings: list of face embeddings
          labels: list of entity names [ID_NAME,...]
        """
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
                labels.append(entity_dir.split('_')[0])

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

    def recognize_image(self, unknown_img, recognizer_model=None, distance_threshold=0.6):
        """ recognize faces in image
        Params:
          unknown_img: image_path or image object(frame) . in batch processing, the param is embeddings of one frame
          recognizer_model: face recognition model  .   interface for build other models on the top of embeddings
        Results:
          detected_faces: list of detected entity names in unknown_img
        """
        detected_faces = []
        unknown_img_embeddings = None

        if isinstance(unknown_img, list):  # batch
            unknown_img_embeddings = unknown_img
        else:  # encode single image
            unknown_img_embeddings = self.represent(unknown_img)

        for unknown_img_embedding in unknown_img_embeddings:  # for each face in the image
            if not recognizer_model:  # run basic recognition
                a = np.matmul(self.embeddings, unknown_img_embedding)
                b = np.linalg.norm(self.embeddings, axis=1)
                c = np.linalg.norm(unknown_img_embedding)
                face_distances = 1 - a / (b * c)
                min_distance = np.min(face_distances)

                if min_distance < distance_threshold:
                    entity = self.labels[np.argmin(face_distances)]
                    detected_faces.append(entity)

                else:
                    # LOGGER.info('face detected but no match')
                    detected_faces.append('unknown')

            else:  # call ANN
                if not recognizer_model.fitted:
                    recognizer_model.fit(embeddings=self.embeddings, labels=self.labels)
                entity = recognizer_model.predict(unknown_img_embedding)
                if entity:
                    detected_faces.append(entity)

        return detected_faces

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

        # faces = self.detector.detect_faces(img)
        # Compatible with the MTCNN from facenet_pytorch
        boxes, confidence, keypoints = self.detector.detect(Image.fromarray(img), landmarks=True)
        faces = [{
            'box': [box[0], box[1], box[2] - box[0], box[3] - box[1]],
            'confidence': confidence,
            'keypoints': {
                'left_eye': tuple(keypoints[0]),
                'right_eye': tuple(keypoints[1]),
                'nose': tuple(keypoints[2]),
                'mouth_left': tuple(keypoints[3]),
                'mouth_right': tuple(keypoints[4]),
            }}
            for box, confidence, keypoints in zip(boxes, confidence, keypoints)]

        face_number = len(faces)

        if return_face_number and face_number != 1:  # for tuning distance threshold
            return face_number

        # get biggest face from thumbnails
        if one_face and face_number > 1:
            height = [face['box'][3] for face in faces]  # box: [x, y, w, h]
            index = height.index(max(height))
            faces = [faces[index]]

        for face in faces:
            aligned_face = face_alignment(img, self.target, face['keypoints'])

            aligned_face = np.expand_dims(aligned_face, axis=0)

            embedding = self.encoder.predict(aligned_face)[0]

            embeddings.append(embedding)

        return embeddings
