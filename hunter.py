import logging
import os
import face_recognition
import cv2
from helpers import path_exists
import pickle

LOGGER = logging.getLogger('fh')


class Hunter(object):
    """
    Hunter

    Can be used to create embeddings of thumbnails and predict entities in videos or images

    Parameters
    ----------
    method: str, default = 'hnsw'
        The method that NMSLIB uses for the k-Nearest Neighbor search.
        Details can be found here: https://github.com/nmslib/nmslib/blob/master/manual/methods.md.

    space: str, default = 'l2'
        The vector space NMSLIB uses for comparing data points.
        Details can be found here: https://github.com/nmslib/nmslib/blob/master/manual/spaces.md.

    model: str, default = 'hog'
        Defines the model of the face recognition library.
        Can be 'hog' or 'CNN'.

    distance_threshold: float, default = 0.4
        Defines the maximum distance face embeddings can have to be detected as similar.

    scaling_x: float, default = 1.0
        Allows to scale frames in x-direction before applying the face recognition.
        May allow faster computations.

    scaling_y: float, default = 1.0
        Allows to scale frames in y-direction before applying the face recognition.
        May allow faster computations.

    Attributes
    ----------
    estimator, default = None
        Contains the reference to the created or loaded NMSLIB-Index.

    labels: list, default = []
        An ordered list of entities. The indices allow to link embeddings in the NMSLIB index to entities.

    """
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
        """ Create embeddings from thumbnails in a folder or load an existing NMSLIB index

        Parameters
        ----------
        thumbnails_path: str, default = './thumbnails
            Path to the directory in which the thumbnails or an existing index are.

        load_data: bool, default = False
            Specifies if new embeddings should be created or an existing index loaded.

        name: str, default = 'index'
            Only necessary if load_data is True. Defines the name of the index to load.

        Returns
        ----------
        self
        """
        import nmslib
        self.estimator = nmslib.init(method=self.method, space=self.space)

        # Check if path points to an existing index of embeddings
        if load_data:
            self.estimator.loadIndex(os.path.join(thumbnails_path, name + '.bin'), True)
            with open(os.path.join(thumbnails_path, f'{name}.txt'), "rb") as fp:
                self.labels = pickle.load(fp)
            if self.estimator is None:
                LOGGER.warning(f'Failed to load embeddings at {thumbnails_path}')
            return self

        # Create embeddings if not
        for entity in os.listdir(thumbnails_path):
            if not os.path.isdir(os.path.join(thumbnails_path, entity)):
                continue

            for image in os.listdir(os.path.join(thumbnails_path, entity)):
                LOGGER.info(f'Encoding {entity}, thumbnail: {image}')
                current_image = cv2.imread(os.path.join(thumbnails_path, entity, image))
                if current_image is None:
                    LOGGER.warning(f'Could not load image {os.path.join(thumbnails_path, entity, image)}')
                    continue

                img = cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB)
                face_encoding = face_recognition.face_encodings(img)
                if len(face_encoding) == 0:
                    LOGGER.warning(
                        f'Could not create encoding for image {os.path.join(thumbnails_path, entity, image)}')
                    continue

                self.estimator.addDataPoint(len(self.labels), face_recognition.face_encodings(img)[0])
                self.labels.append(entity)
        self.estimator.createIndex()

        return self

    def predict(self, file: str = None):
        """ Predict entities in a video or image

        Parameters
        ----------
        file: str, default = None
            The path to the video or image to analyze.

        Returns
        ----------
        y: List of lists, length = number of frames in a video or 1
            Inner lists contain the entities per frame or in an image
        """
        y = []
        frame = None

        LOGGER.info(f'Starting face recognition on {file}')
        cap = cv2.VideoCapture(file)

        while True:
            # Check if file is a video or image
            if cap.isOpened():
                ret, frame = cap.read()

                # Exit when there are no frames anymore
                if not ret:
                    break
            else:
                # Exit if image has already been read. We only want to execute the loop once.
                if frame is not None:
                    break

                frame = cv2.imread(file)

            # Resize the frame for faster computation
            small_frame = cv2.resize(frame, (0, 0), fx=self.scaling_x, fy=self.scaling_y)
            small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Find faces and get their encodings
            face_locations = face_recognition.face_locations(small_frame, model=self.model)

            if len(face_locations) == 0:
                y.append([])
                continue

            face_encodings = face_recognition.face_encodings(small_frame, face_locations)

            # Compare closest entities against threshold
            closest_distances = self.estimator.knnQueryBatch(face_encodings, k=1)
            are_matches = [closest_distances[i][1][0] <= self.distance_threshold for i in
                           range(len(face_locations))]

            faces = []
            for match_id, match_value in enumerate(are_matches):
                if not match_value:
                    pass
                    # faces.append('Unknown')
                else:
                    try:
                        faces.append(self.labels[closest_distances[0][0][match_id]])
                    except IndexError:
                        LOGGER.info('Found more faces than got labels')
            y.append(faces)
        return y

    def save(self, path: str = './config', name: str = 'index'):
        """ Save embeddings of the class locally

        Parameters
        ----------
        path: str, default = './config'
            The path to the folder for the index

        name: str, default = 'index'
            The name of the newly created index.

        Returns
        ----------
        self
        """
        path_exists(path)

        self.estimator.saveIndex(os.path.join(path, name + '.bin'), save_data=True)
        with open(os.path.join(path, name + '.txt'), 'wb') as fp:
            pickle.dump(self.labels, fp)

        return self
