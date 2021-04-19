import logging
import os
import face_recognition
import cv2
import pandas as pd

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

    def fit(self, thumbnails_path: str = './thumbnails'):
        import nmslib
        self.estimator = nmslib.init(method=self.method, space=self.space)

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

    def predict(self, videos_path: str = './videos'):
        videos = pd.read_csv(os.path.join(videos_path, 'information.csv'))
        y = []

        for index, video in videos.iterrows():
            LOGGER.info("Starting face recognition on {}".format(video['video']))
            cap = cv2.VideoCapture(os.path.join(videos_path, video['video']))

            face_names = []
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

                for match_id, match_value in enumerate(are_matches):
                    if not match_value:
                        LOGGER.warning('Unknown identity')
                    elif self.labels[closest_distances[match_id][0][0]] not in face_names:
                        face_names.append(self.labels[closest_distances[0][0][match_id]])

            LOGGER.info("Video {} contained: {}. True value: {}".format(video['video'], face_names, video['entities']))
            y.append(video['entities'])

        return y

    def save(self, path: str = './config/index.txt'):
        path_without_filename = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(path_without_filename):
            LOGGER.info('Creating path {}'.format(path_without_filename))
            os.makedirs(path)

        self.estimator.saveIndex(path, save_data=True)

        return self
