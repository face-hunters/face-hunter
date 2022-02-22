import os
import pickle
import logging
import numpy as np
import cv2
from deepface import DeepFace
from PIL import Image
from deepface.commons import functions
from facenet_pytorch import MTCNN
from src.preprocessing.facial_preprocessing import face_alignment
from src.utils.utils import image_files_in_folder, get_config

LOGGER = logging.getLogger('face-recognition')

on_rtd = os.environ.get('READTHEDOCS') == 'True'
on_flask = os.environ.get('FLASK_running') == 'True'

if on_rtd or on_flask:
    CONFIG = get_config('../src/utils/config.yaml')
else:
    CONFIG = get_config('src/utils/config.yaml')


class FaceRecognition(object):
    """ Allows to recognize faces in videos """

    def __init__(self,
                 thumbnail_list: list = None,
                 thumbnails_path: str = 'data/thumbnails/thumbnails',
                 img_width: int = 500,
                 encoder_name: str = 'ArcFace',
                 labels_path: str = 'data/embeddings/labels.pickle',
                 embeddings_path: str = 'data/embeddings/embeddings.pickle'):
        """ create or load kg_encodings. create detector, encoder

        Args:
            thumbnail_list (list): For sample use.
            thumbnails_path (str): Path to thumbnail directory.
            img_width (int): Scale the image to fixed new width.
            encoder_name (int): Options are "VGG-Face", "Facenet", "OpenFace", "DeepFace", "DeepID", "ArcFace", "Dlib".
            labels_path (str): Path to save and load thumbnail labels
            embeddings_path (str): Path to save and load thumbnail embeddings
        """
        self.thumbnail_list = thumbnail_list
        self.thumbnails_path = thumbnails_path
        self.img_width = img_width
        self.labels_path = labels_path
        self.embeddings_path = embeddings_path
        self.detector = MTCNN(keep_all=True, post_process=False, device=CONFIG['face-recognition']['device'])
        self.encoder = DeepFace.build_model(encoder_name)
        self.target = functions.find_input_shape(self.encoder)  # (150,150) encoder input shape
        self.labels, self.embeddings = self.load_embeddings()  # store the 2 lists in labels.pickle encoddings.pickle

    def recognize_video(self, video_path: str, recognizer_model=None, distance_threshold=0.6, by='second', show_frames: bool = False):
        """ recognize faces on a frame or second level

        Args:
            video_path (str): Path to the video.
            recognizer_model (any model): Model trained with embeddings to predict entities.
            distance_threshold (float): The threshold below which recognitions are marked as unknown.
            by (str): Recognize by 'second' or 'frame'.
            show_frames (bool): Whether each frame should be displayed to the user or not.

        Returns:
            frame_faces_list (list): List of recognized entities per frame/second.
            detected_faces (list): List of identical entities.
            timestamps (float): The corresponding timestamps to the detections.
        """
        if not os.path.exists(video_path):
            LOGGER.info(f'{video_path} does not exists')
        LOGGER.debug(video_path)

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

            if show_frames:
                cv2.imshow('Frame', frame)
                cv2.waitKey()

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

                frame_number += int(fps)
                LOGGER.debug(frame_number)
                video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                success, frame = video.read()

        if len(frames) == 1:
            frame_faces_list.append(self.recognize_image(frames[0], recognizer_model))
        elif len(frames) > 1:
            frame_faces_list.extend(self.batch_recognize_images(frames, recognizer_model))
            frames.clear()

        detected_faces = {entity for l in frame_faces_list for entity in l}

        return detected_faces, frame_faces_list, timestamps

    def batch_recognize_images(self, unknown_imgs: list, recognizer_model=None, distance_threshold=0.6):
        """ Recognize entities in batches of embeddings

        Args:
            unknown_imgs (list): List of embeddings.
            recognizer_model (any model): Model trained with embeddings to predict entities.
            distance_threshold (float): The threshold below which recognitions are marked as unknown.

        Returns:
            detected_faces (list): List of detected entities.
        """
        detected_faces = []
        embeddings = self.batch_represent(unknown_imgs)

        # recognize img by frame
        for frame_embeddings in embeddings:
            detected_faces.append(self.recognize_image(frame_embeddings, recognizer_model, distance_threshold))

        return detected_faces

    def batch_represent(self, imgs: list):
        """ create embeddings from images in batches

        Args:
            imgs (list): List of frames.

        Returns:
            embeddings: List of face embeddings.
        """
        embeddings = []

        mtcnn_imput = [Image.fromarray(img) for img in imgs]

        boxes, confidence, keypoints = self.detector.detect(mtcnn_imput, landmarks=True)
        frames_faces_detection = []

        for i in range(len(boxes)):
            # there is face in the frame
            if boxes[i] is not None and confidence[i] is not None and keypoints[i] is not None:
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
        LOGGER.debug(flat_aligned_faces)
        # batch encoding
        if len(flat_aligned_faces) > 0:  # otherwise, no face in the batch
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
        """ create and save face embeddings and entity labels

        Returns:
            embeddings (list): List of face embeddings.
            labels (list): List of entity names.
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

                if entity_embedding is None:
                    LOGGER.warning(f'Could not create encoding for image {img_path}')
                    continue

                if len(entity_embedding) > 1:
                    LOGGER.warning(f'There are more than one faces in image {img_path}')
                    continue

                embeddings.append(entity_embedding[0])
                labels.append(entity_dir.replace('_', ' '))

                LOGGER.debug(embeddings)

        # write to disk
        with open(self.labels_path, 'wb') as f:
            f.write(pickle.dumps(labels))
        with open(self.embeddings_path, 'wb') as f:
            f.write(pickle.dumps(embeddings))
        return labels, embeddings

    def load_embeddings(self):
        """ Loads already existing embeddings

        Returns:
            labels (list): List of entity names.
            embeddings (list): List of face embeddings.
        """
        if os.path.exists(self.labels_path) and os.path.exists(self.embeddings_path):
            labels = pickle.loads(open(self.labels_path, "rb").read())
            embeddings = pickle.loads(open(self.embeddings_path, "rb").read())
            return labels, embeddings
        return self.create_embeddings()

    def recognize_image(self, unknown_img, recognizer_model=None, distance_threshold=0.6):
        """ Recognize entities in an image

        Args:
            unknown_img (image_path or image object): The image to detect entities in.
            recognizer_model (any model): Model trained with embeddings to predict entities.
            distance_threshold (float): The threshold below which recognitions are marked as unknown.

        Returns:
            detected_faces (list): List of detected entities.
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
        """ create an embedding from an image

        Args:
            img (img object | img_path): The image to create the embedding for.
            one_face (bool): If only the largest face should be considered.
            return_face_number (bool): If the number of faces should be returned for distance tuning.

        Returns:
            embeddings (list): List of face embeddings. OR
            face_number (int): Returns number of faces if return_face_number is True and number of faces > 1.
        """
        embeddings = []

        if isinstance(img, str):  # img is a path
            img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)

        # faces = self.detector.detect_faces(img)
        # Compatible with the MTCNN from facenet_pytorch
        boxes, confidence, keypoints = self.detector.detect(Image.fromarray(img), landmarks=True)

        # If no face is found
        if confidence[0] is None:
            return None

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
