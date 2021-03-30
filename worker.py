import logging
import face_recognition
import cv2
import numpy as np
import os

LOGGER = logging.getLogger('fh')


class Worker(object):
    def __init__(self,
                 thumbnails_path: str = './thumbnails',
                 videos_path: str = './videos'):
        self.thumbnails_path = thumbnails_path
        self.videos_path = videos_path

    # Imports thumbnails
    def read_thumbnails(self):
        images = []
        classes = []
        image_list = os.listdir(self.thumbnails_path)
        for image in image_list:
            current_image = cv2.imread(self.thumbnails_path + '/' + image)
            images.append(current_image)
            classes.append(os.path.splitext(image)[0])
        return images, classes

    # Returns a list of 128dimensional thumbnail encodings
    def get_thumbnail_encodings(self, images):
        encoding_list = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encoding = face_recognition.face_encodings(img)[0]
            encoding_list.append(encoding)
        return encoding_list

    # Learn thumbnail entities and detect them in locally stored videos
    def run_face_detection(self):
        images, classes = self.read_thumbnails()
        encoding_list = self.get_thumbnail_encodings(images)

        # Iterate through videos and apply face recognition
        for video in os.listdir(self.videos_path):
            LOGGER.info("Starting face recognition on {}".format(video))
            cap = cv2.VideoCapture(self.videos_path + '/' + video)
            face_names = []
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                small_frame = cv2.resize(frame, (0, 0), fx=1., fy=1.)
                small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(small_frame)
                face_encodings = face_recognition.face_encodings(small_frame, face_locations)
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(encoding_list, face_encoding)
                    name = "Unknown"
                    face_distances = face_recognition.face_distance(encoding_list, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = classes[best_match_index]
                    if name not in face_names + ['Unknown']:
                        face_names.append(name)
            LOGGER.info("Video {} contained: {}".format(video, face_names))
