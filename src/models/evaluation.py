import itertools
import os
import logging
import pandas as pd
from itertools import chain
import numpy as np
from Levenshtein import distance as levenshtein_distance
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors

LOGGER = logging.getLogger('h')


def evaluate_on_dataset(path: str = 'data/datasets/ytcelebrity', thumbnails: str = '../../data/thumbnails', save_path: str = None, index: str = None):
    """ Detects entities in a dataset and calculates evaluation metrics

    Parameters
    ----------
    args.path: str, default = 'data/datasets/yt-celebrity'
        The Location of the dataset.
    """
    print(thumbnails)
    hunter = ApproximateKNearestNeighbors()

    # Load existing index if desired
    if index is not None:
        hunter.fit(thumbnails, load_data=True, name=self.index)
    else:
        hunter.fit(thumbnails)

    # Save index if desired
    if save_path is not None:
        hunter.save(save_path, self.index)

    # Check for unknown entities in the dataset
    missing_entities = get_missing_entities(os.path.join(path, 'information.csv'), hunter.labels)
    if len(missing_entities) >= 0:
        LOGGER.warning(f'Found known entities: {missing_entities}')

    # Start evaluation
    data = pd.read_csv(os.path.join(path, 'information.csv'))
    total_accuracy = 0
    total_recall = 0
    total_precision = 0
    for index, file in data.iterrows():
        y = hunter.predict(os.path.join(path, file['file']))
        accuracy, recall, precision = get_evaluation_metrics(y,
                                                             list(itertools.repeat(file['entities'], len(y))),
                                                             len(hunter.labels))
        LOGGER.info(f'Accuracy: {accuracy}, Recall: {recall}, Precision: {precision}')
        total_accuracy += accuracy
        total_recall += recall
        total_precision += precision
    total_accuracy = total_accuracy / len(data)
    total_recall = total_recall / len(data)
    total_precision = total_precision / len(data)
    LOGGER.info(f'Total Accuracy: {total_accuracy}, Total Recall: {total_recall}, Total Precision: {total_precision}')


def get_evaluation_metrics(y_pred: list = None,
                           y_true: list = None,
                           num_entities_total: int = None,
                           levenshtein_threshold: int = 0):
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
    y_true = list(map(eval, y_true))
    for index in range(number_predictions):

        true_positives_items = set(np.intersect1d(y_true[index], y_pred[index]))
        true_positives = len(true_positives_items)

        # Check false positive name differences using the levenshtein distance
        if levenshtein_threshold != 0:
            false_positives_items = set(y_pred[index]) - true_positives_items
            for fp_entity in false_positives_items:
                distances = list(map(lambda x: levenshtein_distance(fp_entity, x), true_entities))
                true_positives += len(list(filter(lambda x: x <= levenshtein_threshold, distances)))

        false_positives = len(y_pred[index]) - true_positives
        false_negatives = len(y_true[index]) - true_positives
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


def get_missing_entities(path: str = 'data/datasets/ytcelebrity/information.csv', entities=None):
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
    required = list(chain.from_iterable(data['entities']))
    return list(set(required) - set(entities))
