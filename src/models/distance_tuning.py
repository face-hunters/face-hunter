import os
import re
import logging
import pandas as pd
import numpy as np
from src.utils.utils import check_path_exists
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_text
from src.models.face_recognition import FaceRecognition
from src.data.knowledge_graphs import download_images

LOGGER = logging.getLogger('distance-tuning')


def tune_distance_threshold(video_path='data/datasets/youtube_faces', sample_per_person=5,
                            model='Dlib') -> float:
    """ Finds the optimal distance threshold

    Args:
        video_path (str): Path to the dataset on which the threshold should be investigated
        sample_per_person (int): Number of frames to compare in the data set
        model (str): The face recognition model to tune
  
    Returns:
        distance_threshold (float): The optimal threshold
  """
    csv_path = os.path.join(video_path, 'information.csv')  # { file, entities }

    # 1 clean, match and download thumbnails (Match only names that do not have duplicate names )
    thumbnail_path = 'data/thumbnails/tuning/wikidata_Thumbnails_links.csv'
    thumbnail_dir = 'data/thumbnails/tuning/'
    if not os.path.exists(thumbnail_path):
        LOGGER.info('1/7 cleaning and matching thumbnails...')
        video_df = pd.read_csv(csv_path)
        video_name_df = pd.DataFrame(video_df.entities.unique(), columns=['entities'])
        thumbnail_df = pd.concat([pd.read_csv('data/thumbnails/actor_wikidata_Thumbnails_links.csv'),
                                  pd.read_csv('data/thumbnails/except_actor_wikidata_Thumbnails_links.csv')])

        # clean thumbnails 1 : remove people with the same name
        check_duplicate = thumbnail_df[['norm_name', 'folder_name']].copy().drop_duplicates()
        check_duplicate = check_duplicate.groupby(['norm_name']).size()
        check_duplicate = pd.DataFrame(check_duplicate[check_duplicate == 1].index, columns=['norm_name'])

        video_name_df = video_name_df.merge(check_duplicate, how='inner', left_on='entities',
                                            right_on='norm_name').drop(['norm_name'], axis=1)
        tmp = video_name_df.merge(thumbnail_df, how='inner', left_on='entities', right_on='norm_name')

        # clean thumbnails 2 : Remove the norm_name of multiple people who are regularized into one person
        check_error = tmp[['norm_name', 'name']].copy().drop_duplicates()
        check_error = check_error.groupby(['norm_name']).size()
        check_error = pd.DataFrame(check_error[check_error == 1].index, columns=['norm_name'])

        tmp = tmp.merge(check_error, how='inner')

        check_path_exists(thumbnail_dir)
        tmp.to_csv(thumbnail_path)

        LOGGER.info(f'the distance threshold tuning is running on {len(tmp.name.unique())} celebrities')  # TODO : test
        LOGGER.info('2/7 downloading thumbnails...')
        download_images(path=thumbnail_dir)

    # 2 create thumbnails embeddings
    thumbnails_path = 'data/thumbnails/tuning/thumbnails'
    fr_dir = 'data/embeddings/tuning'

    check_path_exists(fr_dir)
    embeddings_path = os.path.join(fr_dir, 'embeddings.pickle')
    labels_path = os.path.join(fr_dir, 'labels.pickle')

    if os.path.exists(embeddings_path):
        os.remove(embeddings_path)
    if os.path.exists(labels_path):
        os.remove(labels_path)

    LOGGER.info('3/7 creating thumbnails embeddings...')
    fr = FaceRecognition(thumbnails_path=thumbnails_path, encoder_name=model, labels_path=labels_path,
                         embeddings_path=embeddings_path)

    # 3 create train data set
    LOGGER.info('4/7 creating train data set...')
    dataset = pd.DataFrame(fr.labels, columns=['labels'])  # TODO(honglin): only keep ix later
    dataset['ix'] = dataset.index

    # train data set: matching part
    matches = pd.DataFrame(pd.read_csv(thumbnail_path).norm_name.unique(), columns=['entities'])
    video_df = pd.read_csv(csv_path).merge(matches, how='inner')
    sample_frames = video_df.groupby(['entities']).sample(n=sample_per_person, random_state=42)  # { file, entities }

    match_dataset = dataset.merge(sample_frames, how='inner', left_on='labels',
                                  right_on='entities')  # { ix, labels, file, entities }
    match_dataset['identical'] = 1  # { ix, labels, file, entities, identical }
    match_dataset = match_dataset[['ix', 'labels', 'file', 'entities', 'identical']]

    # train data set: unmatched part
    unmatch_data = []

    for i, row in dataset.iterrows():  # for every thumbnail
        ix = row['ix']
        label = row['labels']

        sample_per_thumbnail = match_dataset[match_dataset['labels'] != label].sample(n=sample_per_person,
                                                                                      random_state=42)
        for j, r in sample_per_thumbnail.iterrows():
            unmatch_data.append([ix, label, r['file'], r['entities'], 0])

    unmatch_dataset = pd.DataFrame(unmatch_data, columns=['ix', 'labels', 'file', 'entities', 'identical'])

    dataset = pd.concat([match_dataset, unmatch_dataset]).reset_index(drop=True)

    # 4 create embeddings of frames
    LOGGER.info('5/7 creating embeddings of frames...')

    file_l = []
    frame_embedding_l = []
    remove_number = 0
    for i, row in dataset[dataset['identical'] == 1].iterrows():
        path = row['file']

        if not os.path.exists(path):
            LOGGER.info('{path} does not exist.')
            continue

        if path not in file_l:
            embeddings = fr.represent(path, return_face_number=True)

            if isinstance(embeddings, int):  # the frames that no faces or more than 1 face in
                remove_number += 1
            else:
                file_l.append(path)
                frame_embedding_l.append(embeddings[0])

    LOGGER.info(f'{remove_number} frames contains more than 1 face')
    frame_embeddings = pd.DataFrame({'file': file_l, 'embeddings': frame_embedding_l}).set_index('file')

    # remove those frames from train data set
    dataset = dataset.merge(pd.DataFrame(frame_embeddings.index, columns=['file']), how='inner')

    # balance train dataset
    dataset_match = dataset[dataset['identical'] == 1]
    dataset_unmatch = dataset[dataset['identical'] == 0]

    dataset_match_count = dataset_match.shape[0]
    dataset_unmatch_count = dataset_unmatch.shape[0]

    if dataset_match_count > dataset_unmatch_count:
        dataset_match_downsampled = dataset_match.sample(n=dataset_unmatch_count, random_state=42)
        dataset = pd.concat([dataset_match_downsampled, dataset_unmatch])
    else:
        dataset_unmatch_downsampled = dataset_unmatch.sample(n=dataset_match_count, random_state=42)
        dataset = pd.concat([dataset_match, dataset_unmatch_downsampled])

    # 5s update dataset with distance
    LOGGER.info('6/7 calculating distances...')
    cosine_distances = []
    euclidean_distances = []
    euclidean_l2_distances = []

    for i, row in dataset.iterrows():
        embedding_thumbnail = fr.embeddings[row['ix']]
        embedding_frame = frame_embeddings.loc[row['file'], 'embeddings']

        cosine_distance = 1 - np.matmul(embedding_thumbnail, embedding_frame) / (
                np.linalg.norm(embedding_thumbnail) * np.linalg.norm(embedding_frame))
        cosine_distances.append(cosine_distance)

        euclidean_distance = np.linalg.norm(embedding_thumbnail - embedding_frame)
        euclidean_distances.append(euclidean_distance)

        euclidean_l2_distance = np.linalg.norm(
            embedding_thumbnail / np.linalg.norm(embedding_thumbnail) - embedding_frame / np.linalg.norm(
                embedding_frame))
        euclidean_l2_distances.append(euclidean_l2_distance)

    dataset[
        'cosine_distances'] = cosine_distances  # { ix, labels, file, entities, identical, cosine_distances, euclidean_distances, euclidean_l2_distances }
    dataset['euclidean_distances'] = euclidean_distances
    dataset['euclidean_l2_distances'] = euclidean_l2_distances

    dataset.to_csv('data/datasets/youtube_faces/dataset.csv')  # TODO

    # 6 run decision tree on dataset to get tuned distance threshold, distance as train data, identical as label
    LOGGER.info('7/7 running decision tree and evaluating...')
    dataset = pd.read_csv('data/datasets/youtube_faces/dataset.csv')  # TODO

    for distance in ['cosine_distances', 'euclidean_distances', 'euclidean_l2_distances']:
        decision_tree = DecisionTreeClassifier(max_depth=1)
        decision_tree.fit(dataset[[distance]], dataset[['identical']])
        tree = export_text(decision_tree, feature_names=['distance'])
        LOGGER.info(tree)

        number_pattern = r'\d+.?\d*'
        distance_threshold = float(re.search(number_pattern, tree).group())

        # 7 evaluation
        dataset['prediction'] = 0
        idx = dataset[dataset[distance] <= distance_threshold].index
        dataset.loc[idx, 'prediction'] = 1

        tp = (dataset.prediction & dataset.identical).sum()
        precision = tp / dataset.prediction.sum()
        recall = tp / dataset.identical.sum()
        LOGGER.info(f'{distance} threshold: {distance_threshold}. precision: {precision}. recall: {recall}')

        return distance_threshold
