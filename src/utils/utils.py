import logging
import os

LOGGER = logging.getLogger('h')


def check_path_exists(path: str = None):
    """ Checks if a path exists and creates it if not.

    Parameters
    ----------
    path: str, default = None
        The path to check.
    """
    if path is not None and not os.path.exists(path):
        LOGGER.info(f'Creating path path')
        os.makedirs(path)
