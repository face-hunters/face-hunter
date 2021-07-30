import itertools
import os
import logging
import pandas as pd
from itertools import chain
import numpy as np
import mimetypes
import random
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from src.models.face_recognition import FaceRecognition

LOGGER = logging.getLogger('evaluation')


def evaluate_on_dataset(path: str = 'data/datasets/ytcelebrity',
                        thumbnails: str = 'data/thumbnails/dbpedia_thumbnails',
                        ratio: float = 1.0,
                        seed: int = 42):
    """ Detects entities in a dataset and calculates evaluation metrics

    Parameters
    ----------
    path: str, default = 'data/datasets/ytcelebrity'
        The Location of the dataset.

    thumbnails: str, default = 'data/thumbnails'
        The Location of the thumbnails.

    ratio: float, default = 1.0
        Ratio between thumbnails contained and not contained in the dataset.

    seed: int, default = 42
        Parameter to control randomness for repeatable experiments.
    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))
    entities = data['entities'].apply(eval)
    thumbnails = pd.read_csv(os.path.join(thumbnails, 'Thumbnails_links.csv'))
    thumbnail_entities = thumbnails['name'].dropna().sort_values()

    # Sample Creation
    random.seed(seed)
    number_of_additional_thumbnails = int(len(entities) * ratio)
    thumbnail_sample = list(set(thumbnail_entities) - set(entities))
    if len(thumbnail_entities) >= number_of_additional_thumbnails:
        additional_thumbnails = random.sample(thumbnail_sample, int(len(entities) * ratio))
        thumbnail_sample = entities + additional_thumbnails

    # Model Training
    hunter = FaceRecognition(thumbnail_sample)
    recognizer_model = ApproximateKNearestNeighbors()

    # Check if there are still any thumbnails missing
    required = set(chain.from_iterable(entities))
    missing_entities = required - set(hunter.labels)
    if len(missing_entities) >= 0:
        LOGGER.warning(f'Found unknown entities: {missing_entities}')

    # Evaluation
    scores = np.zeros(4)
    files = []
    per_file_results = []
    for index, file in data.iterrows():
        path_to_file = os.path.join(path, file['file'])
        if mimetypes.guess_type(path_to_file)[0].startswith('video'):
            y = hunter.recognize_video(path_to_file, recognizer_model)[1]
        else:
            y = [hunter.recognize_image(path_to_file, recognizer_model)]
            per_file_results.append(get_evaluation_metrics(y, list(itertools.repeat(file['entities'], len(y))),
                                                           missing_entities))
            files.append(file)
        scores = np.add(scores, per_file_results[-1])

    scores = np.divide(scores, len(data))
    LOGGER.info(f'Total Accuracy: {scores[0]}, Total Precision: {scores[1]}, Total Recall: {scores[2]}, '
                f'Total F1: {scores[3]} ')

    return scores, files, per_file_results


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
