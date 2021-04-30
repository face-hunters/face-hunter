import os
import logging
import numpy as np
import time
import requests
from Levenshtein import distance as levenshtein_distance
from urllib.error import HTTPError

LOGGER = logging.getLogger('h')


def path_exists(path: str = None):
    """ Checks if a path exists and creates it if not.

    Parameters
    ----------
    path: str, default = None
        The path to check.
    """
    if path is not None and not os.path.exists(path):
        LOGGER.info(f'Creating path path')
        os.makedirs(path)


def evaluation_metrics(y_pred: list = None,
                       y_true: list = None,
                       num_entities_total: int = None,
                       levenshtein_threshold: int = 3):
    """ Calculates the accuracy, recall and precision for predictions.

    Parameters
    ----------
    y_pred: list
        The list of lists with predicted entities (Entities per frame).

    y_true: list
        The list of lists with true entities (Entities per frame).

    num_entities_total: int
        The total number of recognizable entities.

    levenshtein_threshold: int, default = 3
        Threshold of the levenshtein distance used to detect false classified false positives
        due to name differences.

    Returns
    ----------
    accuracy: float
        (TP + TN) / (TP + TN + FP + FN)

    recall: float
        TP / (TP + FN)

    precision: float
        TP / (TP + FP)
    """
    if y_true is None or y_pred is None or num_entities_total is None:
        raise Exception('No valid input parameters')

    number_predictions = len(y_pred)
    if number_predictions == 0:
        return 0.0, 0.0, 0.0

    accuracy_sum = 0
    recall_sum = 0
    precision_sum = 0
    for index in range(number_predictions):
        true_entities = eval(y_true[index])  # Convert string to list

        true_positives_items = set(np.intersect1d(eval(y_true[index]), y_pred[index]))
        true_positives = len(true_positives_items)

        # Check false positive name differences using the levenshtein distance
        false_positives_items = set(y_pred[index]) - true_positives_items
        for fp_entity in false_positives_items:
            distances = list(map(lambda x: levenshtein_distance(fp_entity, x), true_entities))
            true_positives += len(list(filter(lambda x: x <= levenshtein_threshold, distances)))

        false_positives = len(y_pred[index]) - true_positives
        false_negatives = len(true_entities) - true_positives
        true_negatives = num_entities_total - true_positives - false_negatives - false_positives
        try:
            accuracy_sum += (true_positives + true_negatives) / num_entities_total
            recall_sum += true_positives / (true_positives + false_negatives)
            precision_sum += true_positives / (true_positives + false_positives)
        except ZeroDivisionError:
            LOGGER.debug('Division by zero during evaluation')
    accuracy = accuracy_sum / number_predictions
    recall_macro = recall_sum / number_predictions
    precision_macro = precision_sum / number_predictions
    return accuracy, recall_macro, precision_macro


def download_thumbnail(index: int, i_thumbnail_url: str, i_path: str, i_file_name: str):
    """Downloads a thumbnail from dbpedia
    Parameters
    ----------
    index: int
        The index of the downloaded thumbnail taken from the thumbnail urls dataframe
    i_thumbnail_url: str
        The url of the downloaded thumbnail
    i_path: str
        The download path
    i_file_name: str
        The file name
    Returns
    ----------
    output: list
        A list containing the index, the thumbnail url and the result outcome (success, HTTPError or UnicodeEncodeError)
    """
    try:
        if index % 10000 == 0:
            LOGGER.info(f'Downloaded {index} thumbnails')
        time.sleep(0.001)
        path_exists(os.path.join(i_path))
        headers = {'user-agent': 'bot'}
        r = requests.get(i_thumbnail_url, headers=headers)
        with open(os.path.join(i_path, i_file_name), 'wb') as f:
            f.write(r.content)
        output = [index, i_thumbnail_url, 'success']
        return output
    except HTTPError:
        os.remove(i_path)
        output = [index, i_thumbnail_url, 'HTTPError']
        return output
    except UnicodeEncodeError:
        os.remove(i_path)
        output = [index, i_thumbnail_url, 'UnicodeEncodeError']
        return output
