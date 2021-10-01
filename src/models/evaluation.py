import itertools
import os
import logging
import pandas as pd
import numpy as np
import mimetypes
import random
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from src.models.face_recognition import FaceRecognition
from src.postprocessing.graph_postprocessing import extract_scenes

LOGGER = logging.getLogger('evaluation')


def evaluate_on_dataset(path: str = 'data/datasets/ytcelebrity',
                        path_thumbnails: str = 'data/thumbnails',
                        ratio: float = 1.0,
                        seed: int = 42,
                        single_true: bool = False,
                        scene_extraction: int = 0):
    """ Detects entities in a dataset and calculates evaluation metrics

    Args:
        path (str): The Location of the dataset.
        path_thumbnails (str): The Location of the thumbnails.
        ratio (float): Ratio between thumbnails contained and not contained in the dataset.
        seed (int): Parameter to control randomness for repeatable experiments.
        single_true (bool): If the evaluation dataset only gives a single label for images with multiple entities.
        scene_extraction: (int): Whether to postprocess detections using the scene extraction algorithm. Disabled with 0.

    Returns:
        scores (list): The evaluation scores. [accuracy, precision, recall, f1]
        files (list): The files that were involved in the evaluation.
        per_file_results (list): The evaluation metrics per file.
    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))
    entities = data['entities']
    thumbnails = pd.read_csv(os.path.join(path_thumbnails, 'Thumbnails_links.csv'))
    thumbnail_entities = thumbnails['norm_name'].dropna().sort_values()
    entities = set(entities)
    thumbnail_entities = set(thumbnail_entities)

    # Sample Creation
    random.seed(seed)
    number_of_additional_thumbnails = int(len(entities) * ratio)
    thumbnail_sample = list(set(thumbnail_entities) - set(entities))
    if len(thumbnail_entities) >= number_of_additional_thumbnails:
        additional_thumbnails = random.sample(thumbnail_sample, int(len(entities) * ratio))
        thumbnail_sample = list(entities) + additional_thumbnails

    # Model Training
    hunter = FaceRecognition(thumbnail_list=thumbnail_sample, thumbnails_path=os.path.join(path_thumbnails, 'thumbnails'))
    recognizer_model = ApproximateKNearestNeighbors()

    # Check if there are still any thumbnails missing
    missing_entities = entities - set(hunter.labels)
    if len(missing_entities) >= 0:
        LOGGER.warning(f'Found unknown entities: {missing_entities}')

    # Evaluation
    scores = np.zeros(4)
    files = []
    per_file_results = []
    for index, file in data.iterrows():
        path_to_file = os.path.join(path, file['file'])
        if mimetypes.guess_type(path_to_file)[0].startswith('video'):
            y = hunter.recognize_video(path_to_file, recognizer_model)
            if scene_extraction != 0:
                scenes = extract_scenes(y[1], y[2], scene_extraction)
                y = []
                for scene in scenes:
                    for name in scene.names:
                        if name not in y:
                            y.append(name)
        else:
            y = [hunter.recognize_image(path_to_file, recognizer_model)]
        per_file_results.append(get_evaluation_metrics(y, list(itertools.repeat([file['entities']], len(y))),
                                                       missing_entities, single_true)) # it is for youtube faces dataset, because 'entities' in the csv file is 
                                                                                       # string instead of 
        files.append(file)
        scores = np.add(scores, per_file_results[-1])

    scores = np.divide(scores, len(data))
    LOGGER.info(f'Total Accuracy: {scores[0]}, Total Precision: {scores[1]}, Total Recall: {scores[2]}, '
                f'Total F1: {scores[3]} ')

    return scores, files, per_file_results


def get_evaluation_metrics(y_pred: list = None,
                           y_true: list = None,
                           missing_entities: set = None,
                           single_true: bool = False):
    """ Calculates the accuracy, recall, precision and f1-score for predictions. Details: https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.364.5612&rep=rep1&type=pdf

    Args:
        y_pred (list): The list of lists with predicted entities (Entities per frame).
        y_true (list): The list of lists with true entities (Entities per frame).
        missing_entities (set): List of entities to be handled as unknown.
        single_true (bool): Whether the evaluation dataset only gives single labels for images with multiple entities.

    Returns:
        scores (np.array): [accuracy, precision, recall, f1]
    """
    frame_count = len(y_pred)
    if missing_entities is None:
        missing_entities = set()

    if frame_count == 0:
        scores = np.empty(4)
        scores[:] = np.NaN
        return scores

    scores = np.zeros(4)
    for index in range(frame_count):
        if single_true:
            if y_true[index][0] in y_pred[index]:
                y_pred[index] = y_true[index]
            elif len(y_pred[index]) > 0:
                y_pred[index] = ['wrong_prediction']

        true_clean = ['unknown' if entity in missing_entities else entity for entity in y_true[index]]

        # Accuracy
        Y_intersection_Z = len(set(np.intersect1d(true_clean, y_pred[index])))
        Y_union_Z = len(np.union1d(true_clean, y_pred[index]))
        scores[0] += Y_intersection_Z / Y_union_Z

        # Precision
        Y = len(y_pred[index])        
        scores[1] += Y_intersection_Z / Y

        # Recall
        Z = len(true_clean)
        scores[2] += Y_intersection_Z / Z

        # F1
        scores[3] += (2 * Y_intersection_Z) / (Z + Y)

    scores = np.divide(scores, frame_count)
    LOGGER.info(f'Accuracy: {scores[0]}, Precision: {scores[1]}, Recall: {scores[2]}, f1: {scores[3]}')
    return scores
