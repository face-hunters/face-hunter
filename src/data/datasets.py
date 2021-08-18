import logging
import os
import tarfile
import wget
import pandas as pd
import scipy
from scipy.io import loadmat
import shutil
from src.utils.utils import check_path_exists
from src.preprocessing.file_preprocessing import name_norm

LOGGER = logging.getLogger('dataset-downloader')


def download_seqamlab_dataset(path: str = 'data/datasets/ytcelebrity'):
    """ Downloads the video dataset ytcelebrity and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here: http://seqamlab.com/youtube-celebrities-face-tracking-and-recognition-dataset/.

    Parameters
    ----------
    path: str, default = data/datasets/ytcelebrity
        Path where the videos and information.csv should be saved.
    """
    check_path_exists(path)

    url = 'http://seqamlab.com/wp-content/uploads/Data/ytcelebrity.tar'
    file = os.path.join(path, 'ytcelebrity.tar')
    LOGGER.info('Downloading Youtube Celebrities Face Tracking and Recognition Data Set')
    wget.download(url, file)
    LOGGER.info('Extracting ...')
    tar = tarfile.open(file)
    tar.extractall(path)
    tar.close()
    os.remove(os.path.join(path, 'ytcelebrity.tar'))

    videos = pd.Series(os.listdir(path))
    information = pd.DataFrame(data={
        'file': videos,
        'entities': name_norm(
            videos.apply(lambda x: [' '.join([k.capitalize() for k in os.path.splitext(path + '/' + x)[0].split('_')[3:5]])]))
    })
    information = information.set_index('file')
    information.to_csv(path + '/information.csv')


def download_imdb_faces_dataset(path: str = 'data/datasets/imdb-faces'):
    """ Downloads the video dataset imdb-face and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here:  https://github.com/fwang91/IMDb-Face.

    !!! Many links are outdated. Only half of the dataset can still be downloaded. !!!

    Parameters
    ----------
    path: str, default = data/datasets/imdb-faces
        Path where the videos and information.csv should be saved.
    """
    imdb_faces = pd.read_csv(os.path.join(path, 'IMDb-Face.csv'))

    entities = []
    total_count = len(imdb_faces)
    for index, row in imdb_faces.iterrows():
        try:
            entity = row['name'].replace('_', ' ')
            LOGGER.info(f'{index}/{total_count}: Downloading image of {entity}')
            wget.download(row['url'], f'./images/imdb-faces/{len(entities)}.jpg')
            entities.append(entity)
        except:
            LOGGER.warning(f'Could not download {row["url"]}')
    information = pd.DataFrame(data={
        'file': range(0, len(entities) - 1),
        'entities': name_norm(entities)
    })
    information = information.set_index('file')
    information.to_csv(os.path.join(path, 'information.csv'))


def download_imdb_wiki_dataset(path: str = 'data/datasets/imdb-wiki'):
    """ Downloads the video dataset imdb-wiki and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/.

    Parameters
    ----------
    path: str, default = data/datasets/imdb-wiki
        Path where the videos and information.csv should be saved
    """
    check_path_exists(path)

    LOGGER.info('Downloading imdb_meta.tar')
    url = 'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_meta.tar'
    file = os.path.join(path, 'imdb_meta.tar')
    wget.download(url, file)
    LOGGER.info('Extracting imdb_meta.tar')
    tar = tarfile.open(file)
    tar.extractall(path)
    tar.close()
    LOGGER.info('Converting imdb.mat to information.csv')
    mat = scipy.io.loadmat(os.path.join(path, 'imdb/imdb.mat'))
    information = pd.DataFrame(data={
        'file': pd.Series(mat['imdb']['full_path'][0][0][0]).apply(lambda x: str(x[0])),
        'entities': name_norm(mat['imdb']['name'][0][0][0])
    })
    information = information.set_index('file')
    information.to_csv(os.path.join(path, 'information.csv'))
    LOGGER.info('Removing unnecessary files')
    os.remove(os.path.join(path, 'imdb_meta.tar'))
    shutil.rmtree(os.path.join(path, 'imdb'))

    LOGGER.info('-- Dataset requires about 300GB free space --')
    urls = [
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_0.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_1.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_2.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_3.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_4.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_5.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_6.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_7.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_8.tar',
        'https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/static/imdb_9.tar'
    ]
    for part, url in enumerate(urls, start=1):
        LOGGER.info(f'Downloading part {part}/9')
        file = os.path.join(path, f'imdb_{str(part)}.tar')
        wget.download(url, file)
        LOGGER.info(f'Extracting part {part}/9')
        tar = tarfile.open(file)
        tar.extractall(path)
        tar.close()


def download_youtube_faces_db(path: str = 'data/datasets/youtube-faces-db'):
    """ Parses a information.csv for the youtube-faces-db dataset. A homogeneous format for evaluation.
        Details about the dataset can be found here: https://www.cs.tau.ac.il/~wolf/ytfaces/.

    !!! Dataset must be downloaded manually from https://www.cs.tau.ac.il/~wolf/ytfaces/.

    Parameters
    ----------
    path: str, default = data/datasets/youtube-faces-db
        Path where the videos are located and the information.csv should be saved at.
    """
    check_path_exists(path)

    videos = []
    entities = []
    for entity in os.listdir(path):
        entity_path = os.path.join(path, entity)
        entity = entity.replace('_', ' ')

        if entity.startswith('.'):
            continue

        for movie in os.listdir(entity_path):
            if movie.startswith('.'):
                continue

            movie_path = os.path.join(entity_path, movie)
            for frame in os.listdir(movie_path):
                if frame.startswith('.'):
                    continue

                videos.append(os.path.join(movie_path, frame))
                entities.append(entity)

    information = pd.DataFrame(data={
        'file': videos,
        'original_entities': entities
    })

    entities_df = pd.DataFrame(information.original_entities.unique(), columns=['original_entities'])
    entities_df['entities'] = name_norm(entities_df.original_entities.tolist())
    information = information.merge(entities_df, how='left', on='original_entities')
    
    information[['file', 'entities']].to_csv(os.path.join(path, 'information.csv'))
