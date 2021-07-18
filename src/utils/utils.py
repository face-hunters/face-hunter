import logging
import os
from typing import Tuple
import yaml
import re
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage import Client
from mtcnn import MTCNN
import cv2
import glob

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


def upload_folder(input_dictionary: str, cloud_config: str, cloud_bucket: str):
    """ Uploads every file in a dictionary to the google cloud storage
    """
    return [upload_file(os.path.join(input_dictionary, file), cloud_config, cloud_bucket, file.split(input_dictionary)[1]) for file in glob.iglob(input_dictionary + '**/**', recursive=True)]


def upload_file(input_file: str, cloud_config: str, cloud_bucket: str, name: str) -> Tuple[str, str]:
    """ Uploads a local file to the google cloud storage

    Parameters
    ----------
    input_file: str
        Path to the local file to upload

    cloud_config: dict
        JSON-string of the cloud credentials

    cloud_bucket: str
        Name of the google cloud bucket

    name: str
        Filename with ending that should be written to the cloud

    Returns
    ----------
    Tuple
        path to the local and remote file
    """
    if cloud_config is None or cloud_bucket is None:
        return input_file, input_file

    client: Client = storage.Client.from_service_account_json(cloud_config)

    try:
        client.get_bucket(cloud_bucket)
    except NotFound:
        client.create_bucket(cloud_bucket)

    if name is  None:
        name = input_file.split('/')[-1:]
    try:
        LOGGER.debug(f'Uploading {input_file} to S3')

        bucket = client.get_bucket(cloud_bucket)
        blob = bucket.blob(name)
        blob.upload_from_filename(input_file)

        remote_path = f'{cloud_bucket}/{name}'
        return input_file, remote_path
    except GoogleAPICallError as e:
        LOGGER.error('An error occurred trying to upload to Google Storage.'
                     f'The following error has been returned: {e}')


def download_file(path: str, cloud_config: str = None, cloud_bucket: str = None, name: str = None) -> str:
    """ Downloads a file from the google cloud storage

    Parameters
    ----------
    path: str
        Path to a local dictionary

    cloud_config: dict
        JSON-string of the cloud credentials

    cloud_bucket: str
        Name of the google cloud bucket

    name: str
        Name of the file in the cloud

    Returns
    ----------
    path: str
        Path to the downloaded local file
    """
    if not os.path.isfile(path):
        if cloud_config is None:
            raise FileNotFoundError(f'{path} does not exist')
        else:
            LOGGER.info(f'Downloading {name} to {path}')
            try:
                client: Client = storage.Client.from_service_account_json(cloud_config)
                bucket = client.get_bucket(cloud_bucket)
                blob = bucket.get_blob(name)
                if blob is None:
                    raise FileNotFoundError(f'File {path} does not exist')

                with open(path, 'wb') as f:
                    blob.download_to_file(f)

            except GoogleAPICallError as e:
                LOGGER.error('An error occurred trying to download from Google Storage.'
                             f'The following error has been returned: {e}')

    return path
