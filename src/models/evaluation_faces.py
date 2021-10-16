import itertools
import os
import logging
import pandas as pd
from itertools import chain
import numpy as np
import mimetypes
import random
import pickle
from src.models.approximate_k_nearest_neighbors import ApproximateKNearestNeighbors
from src.models.face_recognition import FaceRecognition
from src.postprocessing.graph_postprocessing import extract_scenes

LOGGER = logging.getLogger('evaluation')


def evaluate_on_dataset(path: str = '.',
                        path_thumbnails: str = 'data/thumbnails',):
    """ Evaluate the model on youtube faces dataset on video level

    Parameters
    ----------
    path: str, default = 'data/datasets/youtube-faces-db'
        The Location of the dataset.

    thumbnails: str, default = 'data/thumbnails'
        The Location of the thumbnails.

    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))
    entities = data['entities']
  

    # Model Training
    hunter = FaceRecognition( thumbnails_path=os.path.join(path_thumbnails, 'thumbnails_20'))
    recognizer_model = ApproximateKNearestNeighbors()

    # Check if there are still any thumbnails missing
    # required = set(chain.from_iterable(entities))
    # missing_entities = required - set(hunter.labels)
    # if len(missing_entities) >= 0:
    #     LOGGER.warning(f'Found unknown entities: {missing_entities}')

    # Evaluation
    scores = np.zeros(4)
    files = []
    per_file_results = []
    count_video = 0
    correct_video = 0
    entity_list = set(hunter.labels)
    incorrect_video = []
    for index, file in data.iterrows():
        entity = file['entities']
        if entity not in entity_list:
            continue
        path_to_video = os.path.join('..',*file['file'].split('/')[2:-2])
        print(path_to_video)
        for video in os.listdir(path_to_video):
            if os.path.isfile(os.path.join(path_to_video,video)):
                continue
            incorrect_video.append(os.path.join(path_to_video,video))
            count_video = count_video + 1
            correct = 0
            frame_list = os.listdir(os.path.join(path_to_video,video))
            for frame in frame_list:
                y = hunter.recognize_image(os.path.join(path_to_video,video,frame), recognizer_model)
                if entity in y:
                    print(f'{entity} found in {frame}')
                    correct = correct + 1
                else:
                    print(f'{entity} not found in {frame}')
                if np.divide(correct,len(frame_list)) > 0.1 or correct > 1:
                    LOGGER.info(f'{entity} is recognized in {video}')
                    correct_video = correct_video + 1
                    incorrect_video.remove(os.path.join(path_to_video,video))
                    break
            print(f'correct video:{correct_video}, total video:{count_video}')
        entity_list.remove(entity)
    LOGGER.info(f'There are {count_video} videos evaluated, in which {correct_video} are correctly recognized. The accuracy is {np.divide(correct_video,count_video)}')
    with open('incorrect_videos.pickle', 'wb') as f:
        f.write(pickle.dumps(incorrect_video))