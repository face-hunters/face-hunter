import itertools
import os
import logging
import pandas as pd
from itertools import chain
import numpy as np
import mimetypes
from models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from models.face_recognition import FaceRecognition

LOGGER = logging.getLogger('evaluation')


def evaluate_on_dataset(path: str = 'data/datasets/ytcelebrity', thumbnails: str = 'data/thumbnails'):
    """ Detects entities in a dataset and calculates evaluation metrics

    Parameters
    ----------
    path: str, default = 'data/datasets/ytcelebrity'
        The Location of the dataset.

    thumbnails: str, default = 'data/thumbnails'
        The Location of the thumbnails.
    """
    hunter = FaceRecognition(thumbnails)
    recognizer_model = ApproximateKNearestNeighbors()
    data = pd.read_csv(os.path.join(path, 'information.csv'))

    missing_entities = get_missing_entities(os.path.join(path, 'information.csv'), hunter.labels)
    if len(missing_entities) >= 0:
        LOGGER.warning(f'Found unknown entities: {missing_entities}')

    scores = np.zeros(4)
    for index, file in data.iterrows():
        path_to_file = os.path.join(path, file['file'])
        if mimetypes.guess_type(path_to_file)[0].startswith('video'):
            y = hunter.recognize_video(path_to_file, recognizer_model)[1]
        else:
            y = [hunter.recognize_image(path_to_file, recognizer_model)]
        scores = np.add(scores, get_evaluation_metrics(y, list(itertools.repeat(file['entities'], len(y))), missing_entities))

    scores = np.divide(scores, len(data))
    LOGGER.info(f'Total Accuracy: {scores[0]}, Total Precision: {scores[1]}, Total Recall: {scores[2]}, '
                f'Total F1: {scores[3]} ')


def get_evaluation_metrics(y_pred: list = None,
                           y_true: list = None,
                           missing_entities: set = None):
    """ Calculates the accuracy, recall and precision for predictions.
    Details: https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.364.5612&rep=rep1&type=pdf

    Parameters
    ----------
    y_pred: list
        The list of lists with predicted entities (Entities per frame).

    y_true: list
        The list of lists with true entities (Entities per frame).

    missing_entities: set, default = None
        List of entities to be handled as unknown.

    Returns
    ----------
    scores: np.array
        [accuracy, precision, recall, f1]
    """
    frame_count = len(y_pred)
    y_true = list(map(eval, y_true))

    if frame_count == 0:
        scores = np.empty(4)
        scores[:] = np.NaN
        return scores

    scores = np.zeros(4)
    for index in range(frame_count):
        true_clean = ['unknown' if entity in missing_entities else entity for entity in y_true[index]]

        # Accuracy
        Y_intersection_Z = len(set(np.intersect1d(true_clean, y_pred[index])))
        Y_union_Z = len(np.union1d(true_clean, y_pred[index]))
        scores[0] += Y_intersection_Z / Y_union_Z

        # Precision
        Z = len(true_clean)
        scores[1] += Y_intersection_Z / Z

        # Recall
        Y = len(y_pred[index])
        scores[2] += Y_intersection_Z / Y

        # F1
        scores[3] += (2 * Y_intersection_Z) / (Z + Y)

    scores = np.divide(scores, frame_count)
    LOGGER.info(f'Accuracy: {scores[0]}, Precision: {scores[1]}, Recall: {scores[2]}, f1: {scores[3]}')
    return scores


def get_missing_entities(path: str = 'data/datasets/ytcelebrity/information.csv', entities=None) -> set:
    """ Checks if all entities from the information.csv are in the entity-list

    Parameters
    ----------
    path: str
        Path to the information.csv

    entities: list
        List of loaded entities

    Returns
    ----------
    list
        List of unknown entities in the information.csv
    """
    data = pd.read_csv(path)
    data['entities'] = data['entities'].apply(eval)
    required = set(chain.from_iterable(data['entities']))
    return required - set(entities)
