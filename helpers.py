import os
import logging

LOGGER = logging.getLogger('h')


def path_exists(path: str):
    if not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)


def calculate_accuracy(y_pred: list, y_true: list):
    if len(y_pred) == 0:
        return 0.0

    true = 0
    for index in range(len(y_pred)):
        if eval(y_pred[index]) == y_true[index]:
            true += 1
    return true/len(y_pred)
