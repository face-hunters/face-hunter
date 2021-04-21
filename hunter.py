import logging
import os
import face_recognition
import cv2
from helpers import path_exists
import pickle

LOGGER = logging.getLogger('fh')


class Hunter(object):
    def __init__(self,
                 method: str = 'hnsw',
                 space: str = 'l2',
                 model: str = 'hog',
                 distance_threshold: float = 0.4,
                 scaling_x: float = 1.0,
                 scaling_y: float = 1.0):
        self.method = method
        self.space = space
        self.model = model
        self.distance_threshold = distance_threshold
        self.scaling_x = scaling_x
        self.scaling_y = scaling_y
        self.estimator = None
        self.labels = []

    def fit(self, thumbnails_path: str = './thumbnails', load_data: bool = False, name: str = 'index'):
        import nmslib
        self.estimator = nmslib.init(method=self.method, space=self.space)

        # Check if path points to an existing index of embeddings
        if load_data:
            self.estimator.loadIndex(os.path.join(thumbnails_path, name + '.bin'), True)
            with open(os.path.join(thumbnails_path, name + '.txt'), "rb") as fp:
                self.labels = pickle.load(fp)
            if self.estimator is None:
                LOGGER.warning('Failed to load embeddings at {}')
            return self

        # Create embeddings if not
        for identity in os.listdir(thumbnails_path):
            if not os.path.isdir(os.path.join(thumbnails_path, identity)):
                continue

            for image in os.listdir(os.path.join(thumbnails_path, identity)):
                LOGGER.info('Encoding {}, thumbnail: {}'.format(identity, image))
                current_image = cv2.imread(os.path.join(thumbnails_path, identity, image))
                if current_image is None:
                    LOGGER.warning('Could not load image {}'.format(os.path.join(thumbnails_path, identity, image)))
                    continue

                img = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)
                face_encoding = face_recognition.face_encodings(img)
                if len(face_encoding) == 0:
                    LOGGER.warning(
                        'Could not create encoding for image {}'.format(os.path.join(thumbnails_path, identity, image)))
                    continue

                self.estimator.addDataPoint(len(self.labels), face_recognition.face_encodings(img)[0])
                self.labels.append(identity)
        self.estimator.createIndex()

        return self

    def predict(self, file: str = './videos/video.avi'):
        y = []

        LOGGER.info("Starting face recognition on {}".format(file))
        cap = cv2.VideoCapture(file)

        while cap.isOpened():
            ret, frame = cap.read()

            # Exit when there's no frame
            if not ret:
                break

            # Resize the frame for faster computation
            small_frame = cv2.resize(frame, (0, 0), fx=self.scaling_x, fy=self.scaling_y)
            small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Find faces and get their encodings
            face_locations = face_recognition.face_locations(small_frame, model=self.model)

            if len(face_locations) == 0:
                continue

            face_encodings = face_recognition.face_encodings(small_frame, face_locations)

            # Compare closest identities against threshold
            closest_distances = self.estimator.knnQueryBatch(face_encodings, k=1)
            are_matches = [closest_distances[i][1][0] <= self.distance_threshold for i in
                           range(len(face_locations))]

            faces = []
            for match_id, match_value in enumerate(are_matches):
                if not match_value:
                    faces.append('Unknown')
                else:
                    faces.append(self.labels[closest_distances[0][0][match_id]])
                y.append(faces)
        return y

    def save(self, path: str = './config', name: str = 'index'):
        path_exists(path)

        self.estimator.saveIndex(os.path.join(path, name + '.bin'), save_data=True)
        with open(os.path.join(path, name + '.txt'), 'wb') as fp:
            pickle.dump(self.labels, fp)

        return self
