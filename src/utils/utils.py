import logging
import os
import yaml
import  re
from mtcnn import MTCNN
import cv2

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


def get_config(path: str = '/root/FACE-HUNTER/src/utils/config.yaml'):
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


def face_number(img, detector=MTCNN()):
    """ caculate how many faces in img, for download thumbnails use

    if you have to detect many image, you can create a detector then pass to this function:
      detector = MTCNN()
      for img in img_list:
        face_number = face_number('img.jpg', detector)

    params:
      img: can be img object or img path

    return:
      face number in the img
    """
    if isinstance(img, str):
        img = cv2.cvtColor(cv2.imread(img), cv2.COLOR_BGR2RGB)

    faces = detector.detect_faces(img)
    return len(faces)


def image_files_in_folder(folder):
    """ Searches for images in a folder

    Parameters
    ----------
    folder: str, default = None
        The path to the dictionary

    Returns
    ----------
    list
        paths to images
    """
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]
