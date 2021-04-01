import logging
import os

import face_recognition
import cv2
import numpy as np
import pandas as pd

LOGGER = logging.getLogger('fh')


class Worker(object):
    def __init__(self,
                 thumbnails_path: str = './thumbnails',
                 videos_path: str = './videos'):
        self.thumbnails_path = thumbnails_path
        self.videos_path = videos_path
        self.embeddings = []
        self.classes = []

    def load_encodings(self):
        image_list = os.listdir(self.thumbnails_path)
        for image in image_list:
            if not image.startswith('.'):
                current_image = cv2.imread(self.thumbnails_path + '/' + image)
                img = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)
                self.embeddings.append(face_recognition.face_encodings(img)[0])
                self.classes.append(os.path.splitext(image)[0])

    def run_face_detection(self):
        videos = pd.read_csv(self.videos_path + '/information.csv')

        for index, video in videos.iterrows():
            LOGGER.info("Starting face recognition on {}".format(video['video']))
            cap = cv2.VideoCapture(self.videos_path + '/' + video['video'])

            face_names = []
            while cap.isOpened():
                ret, frame = cap.read()

                # Exit when there's no frame
                if not ret:
                    break

                # Resize the frame for faster computation
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                # Find faces and get their encodings
                face_locations = face_recognition.face_locations(small_frame)
                face_encodings = face_recognition.face_encodings(small_frame, face_locations)

                for encoding in face_encodings:
                    name = "Unknown"
                    face_distances = face_recognition.face_distance(self.embeddings, encoding)
                    best_match_index = np.argmin(face_distances)
                    matches = face_recognition.compare_faces(self.embeddings, encoding)
                    if matches[best_match_index]:
                        name = self.classes[best_match_index]

                    if name not in face_names + ['Unknown']:
                        face_names.append(name)
            LOGGER.info("Video {} contained: {}. True value: {}".format(video['video'], face_names, video['entities']))
