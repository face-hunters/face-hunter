import os
import logging
import numpy as np

LOGGER = logging.getLogger('h')


def path_exists(path: str = None):
    """ Checks if a path exists and creates it if not.

    Parameters
    ----------
    path: str, default = None
        The path to check.
    """
    if path is not None and not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)


def evaluation_metrics(y_pred: list = None, y_true: list = None, num_entities: int = None):
    """ Calculates the accuracy, recall and precision for predictions.

    Parameters
    ----------
    y_pred: list
        The list of lists with predicted entities (Entities per frame).

    y_true: list
        The list of lists with true entities (Entities per frame).

    num_entities: int
        The total number of recognizable entities.

    Returns
    ----------
    accuracy: float
        (TP + TN) / (TP + TN + FP + FN)

    recall: float
        TP / (TP + FN)

    precision: float
        TP / (TP + FP)
    """
    if y_true is None or y_pred is None or num_entities is None:
        raise Exception('No valid input parameters')

    if len(y_pred) == 0:
        return 0.0, 0.0, 0.0

    accuracy_sum = 0
    recall_sum = 0
    precision_sum = 0
    for index in range(len(y_pred)):
        true_positives = len(np.intersect1d(eval(y_true[index]), y_pred[index]))
        false_positives = len(y_pred[index]) - true_positives
        false_negatives = len(eval(y_true[index])) - true_positives
        true_negatives = num_entities - true_positives - false_negatives - false_positives
        try:
            accuracy_sum += (true_positives + true_negatives) / num_entities
            recall_sum += true_positives / (true_positives + false_negatives)
            precision_sum += true_positives / (true_positives + false_positives)
        except ZeroDivisionError:
            LOGGER.debug('Division by zero during evaluation')
    accuracy = accuracy_sum / len(y_pred)
    recall_macro = recall_sum / len(y_pred)
    precision_macro = precision_sum / len(y_pred)
    return accuracy, recall_macro, precision_macro
