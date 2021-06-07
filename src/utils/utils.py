import logging
import os
import yaml

LOGGER = logging.getLogger('utils')


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


def get_config(path: str = 'config.yaml'):
    """ Loads the configuration file to a dictionary

    Parameters
    ----------
    path: str, default = None
        The path to the configuration file.

    Returns
    ----------
    config: Dictionary
        The loaded parameters
    """
    with open(path) as f:
        config = yaml.safe_load(f)
    return config
