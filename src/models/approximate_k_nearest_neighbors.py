import os

import numpy as np
import nmslib
import logging

LOGGER = logging.getLogger('approximate_k_neighbors')


class ApproximateKNearestNeighbors(object):
    """
    ApproximateKNearestNeighbors

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

    Attributes
    ----------
    estimator, default = None
        Contains the reference to the created or loaded NMSLIB-Index.

    labels: list, default = []
        An ordered list of entities. The indices allow to link embeddings in the NMSLIB index to entities.

    """

    def __init__(self,
                 method='hnsw',
                 space='cosinesimil',
                 model='hog',
                 distance_threshold=0.4,
                 index_path='data/embeddings/index.bin',
                 k=1
                 ):
        self.method = method
        self.space = space
        self.model = model
        self.recognizer = None
        self.index_path = index_path
        self.labels = []
        self.distance_threshold = distance_threshold
        self.k = k
        self.fitted = False

    def fit(self, embeddings, labels):
        """ Transform the embeddings into the index parameter of nmslib

        Parameters
        ----------
        embeddings: list,
            The embeddings of all face images.
        labels: list,
            List of entities in our datasets

        Returns
        ----------
        self
        """
        self.recognizer = nmslib.init(method=self.method, space=self.space, data_type=nmslib.DataType.DENSE_VECTOR)
        self.labels = labels

        # If there exists index for nmslib, load it
        if os.path.exists(self.index_path):
            self.recognizer.loadIndex(self.index_path)

        # If not, create new index based on the embeddings
        else:
            # Transform the embeddings list into numpy array for nmslib
            embeddings = np.array(embeddings)
            self.recognizer.addDataPointBatch(embeddings)
            index_time_params = {'M': 15, 'indexThreadQty': 4, 'efConstruction': 100}
            self.recognizer.createIndex(index_time_params)
            self.recognizer.saveIndex(self.index_path, save_data=False)
        self.fitted = True
        return self

    def predict(self, embedding):
        """ Predict entity of embedding
        Parameters
        ----------
        embedding:
            The embedding to analyze
        Returns
        ----------
        The entity with maximum probability to match the embedding
        """
        entities = []
        embedding = np.expand_dims(embedding, axis=0)
        neighbors, distances = self.recognizer.knnQueryBatch(embedding, k=self.k, num_threads=4)[0]

        for i in range(self.k):
            if distances[i] < self.distance_threshold:
                idx = neighbors[0]
                entity = self.labels[idx]
                entities.append(entity)
            return max(entities, key=entities.count)
