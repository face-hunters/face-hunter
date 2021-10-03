import os

import numpy as np
import nmslib
import logging

LOGGER = logging.getLogger('approximate_k_neighbors')


class ApproximateKNearestNeighbors(object):
    """ Provides a fast way to perform k-Nearest-Neighbor-search to predict entities in videos or images

    Args:
        method (str): The method that NMSLIB uses for the k-Nearest Neighbor search. Details can be found here: https://github.com/nmslib/nmslib/blob/master/manual/methods.md.
        space (str): The vector space NMSLIB uses for comparing data points. Details can be found here: https://github.com/nmslib/nmslib/blob/master/manual/spaces.md.
        distance_threshold (float): Defines the maximum distance face embeddings can have to be detected as similar.
        index_path (str): Optional path to an existing model to load.
        k (int): The number of nearest neighbors to consider.
    """

    def __init__(self,
                 method='hnsw',
                 space='cosinesimil',
                 distance_threshold=0.4,
                 index_path='data/embeddings/index.bin',
                 k=1
                 ):
        self.method = method
        self.space = space
        self.recognizer = None
        self.index_path = index_path
        self.labels = []
        self.distance_threshold = distance_threshold
        self.k = k
        self.fitted = False

    def fit(self, embeddings, labels):
        """ Uses embeddings to train the algorithm.

        Args:
            embeddings (list): The ordered embeddings of all face images.
            labels (list): Ordered List of entities in our datasets

        Returns:
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
            LOGGER.debug(embeddings)
            self.recognizer.addDataPointBatch(embeddings)
            index_time_params = {'M': 15, 'indexThreadQty': 4, 'efConstruction': 100}
            self.recognizer.createIndex(index_time_params)
            self.recognizer.saveIndex(self.index_path, save_data=False)
        self.fitted = True
        return self

    def predict(self, embedding):
        """ Predict the entity of an embedding

        Args:
            embedding: The embedding to analyze

        Returns:
            entity (str): The entity with maximum probability to match the embedding
        """
        entities = []
        embedding = np.expand_dims(embedding, axis=0)
        neighbors, distances = self.recognizer.knnQueryBatch(embedding, k=self.k, num_threads=4)[0]

        for i in range(self.k):
            if distances[i] < self.distance_threshold:
                idx = neighbors[0]
                entity = self.labels[idx]
                entities.append(entity)

        if entities:
            return max(entities, key=entities.count)
        else:
            return 'unknown'
