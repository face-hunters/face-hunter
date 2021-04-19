import os
import logging

LOGGER = logging.getLogger('h')


def path_exists(path: str):
    if not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)
