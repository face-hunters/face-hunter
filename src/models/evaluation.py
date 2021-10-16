import itertools
import os
import logging
import pandas as pd
import numpy as np
import mimetypes
import random
import pickle
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
    hunter = FaceRecognition(thumbnail_list=thumbnail_sample,
                             thumbnails_path=os.path.join(path_thumbnails, 'thumbnails'))
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
                                                       missing_entities,
                                                       single_true))  # it is for youtube faces dataset, because 'entities' in the csv file is
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


def evaluate_youtube_faces_on_video_level(path: str = '.',
                                          path_thumbnails: str = 'data/thumbnails', ):
    """ Evaluate the model on youtube faces dataset on video level

    Parameters
    ----------
    path: str, default = 'data/datasets/youtube-faces-db'
        The Location of the dataset.

    path_thumbnails: str, default = 'data/thumbnails'
        The Location of the thumbnails.

    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))

    # Model Training
    hunter = FaceRecognition(thumbnails_path=os.path.join(path_thumbnails, 'thumbnails_20'))
    recognizer_model = ApproximateKNearestNeighbors()

    # Evaluation
    count_video = 0
    correct_video = 0
    entity_list = set(hunter.labels)
    incorrect_video = []
    for index, file in data.iterrows():
        entity = file['entities']
        if entity not in entity_list:
            continue
        path_to_video = os.path.join('..', *file['file'].split('/')[2:-2])
        LOGGER.debug(path_to_video)
        for video in os.listdir(path_to_video):
            if os.path.isfile(os.path.join(path_to_video, video)):
                continue
            incorrect_video.append(os.path.join(path_to_video, video))
            count_video = count_video + 1
            correct = 0
            frame_list = os.listdir(os.path.join(path_to_video, video))
            for frame in frame_list:
                y = hunter.recognize_image(os.path.join(path_to_video, video, frame), recognizer_model)
                if entity in y:
                    LOGGER.info(f'{entity} found in {frame}')
                    correct = correct + 1
                else:
                    LOGGER.warning(f'{entity} not found in {frame}')
                if np.divide(correct, len(frame_list)) > 0.1 or correct > 1:
                    LOGGER.info(f'{entity} is recognized in {video}')
                    correct_video = correct_video + 1
                    incorrect_video.remove(os.path.join(path_to_video, video))
                    break
            LOGGER.info(f'correct video:{correct_video}, total video:{count_video}')
        entity_list.remove(entity)
    LOGGER.info(
        f'There are {count_video} videos evaluated, in which {correct_video} are correctly recognized. The accuracy is {np.divide(correct_video, count_video)}')
    with open('incorrect_videos.pickle', 'wb') as f:
        f.write(pickle.dumps(incorrect_video))
