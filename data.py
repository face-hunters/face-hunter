import logging
import os
import tarfile
import wget
from pytube import YouTube
import pandas as pd
import scipy
from scipy.io import loadmat
import shutil
from helpers import path_exists

LOGGER = logging.getLogger('d')


def download_youtube_videos(urls: str = None, path: str = './videos/youtube'):
    """ Downloads videos from youtube and parses an information.csv. A homogeneous format for evaluation.
        The method allows to create own evaluation datasets.

    Parameters
    ----------
    urls: str, default = None
        Location of a text-file containing line-wise URLs of youtube videos and entities that occur in it.
        Format should be: <url>;<entity1>,<entity2>,..

    path: str, default = ./videos/youtube'
        Path where the videos and information.csv should be saved.
    """
    path_exists(path)

    videos = []
    entities = []
    with open(urls) as f:
        for line in f:
            line = line.strip()
            video = line.split(';')
            yt = YouTube(video[0])
            LOGGER.info('Starting to download ' + yt.title)
            videos.append(yt.title + '.mp4')
            entities.append(video[1].split(','))
            yt.streams.filter(progressive=True, file_extension='mp4').order_by(
                'resolution').desc().first().download(path)

    information = pd.DataFrame(data={
        'file': videos,
        'entities': entities
    })
    information = information.set_index('file')
    if os.path.exists(os.path.join(path + '/information.csv')):
        information = pd.read_csv(os.path.join(path + '/information.csv')).set_index('video').append(information)
    information.to_csv(os.path.join(path + '/information.csv'))


def download_seqamlab_dataset(path: str = './videos/ytcelebrity'):
    """ Downloads the video dataset ytcelebrity and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here: http://seqamlab.com/youtube-celebrities-face-tracking-and-recognition-dataset/.

    Parameters
    ----------
    path: str, default = ./videos/ytcelebrity'
        Path where the videos and information.csv should be saved.
    """
    path_exists(path)

    url = 'http://seqamlab.com/wp-content/uploads/Data/ytcelebrity.tar'
    file = path + '/ytcelebrity.tar'
    LOGGER.info('Downloading Youtube Celebrities Face Tracking and Recognition Data Set')
    wget.download(url, file)
    LOGGER.info('Extracting ...')
    tar = tarfile.open(file)
    tar.extractall(path)
    tar.close()
    os.remove(os.path.join(path, '/ytcelebrity.tar'))

    videos = pd.Series(os.listdir(path))
    information = pd.DataFrame(data={
        'file': videos,
        'entities': videos.apply(lambda x: [' '.join(os.path.splitext(path + '/' + x)[0].split('_')[3:5])])
    })
    information = information.set_index('file')
    information.to_csv(path + '/information.csv')


def download_imdb_faces_dataset(path: str = './images/imdb-faces'):
    """ Downloads the video dataset imdb-face and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here:  https://github.com/fwang91/IMDb-Face.

    !!! Many links are outdated. Only half of the dataset can still be downloaded. !!!

    Parameters
    ----------
    path: str, default = ./videos/ytcelebrity'
        Path where the videos and information.csv should be saved.
    """
    imdb_faces = pd.read_csv(os.path.join(path, 'IMDb-Face.csv'))

    entities = []
    total_count = len(imdb_faces)
    for index, row in imdb_faces.iterrows():
        try:
            entity = row['name'].replace('_', ' ').lower()
            LOGGER.info('{}/{}: Downloading image of {}'.format(index, total_count, entity))
            wget.download(row['url'], './images/imdb-faces/{}.jpg'.format(len(entities)))
            entities.append(entity)
        except:
            LOGGER.warning('Could not download {}'.format(row['url']))
    information = pd.DataFrame(data={
        'file': range(0, len(entities) - 1),
        'entities': entities
    })
    information = information.set_index('file')
    information.to_csv(path + '/information.csv')


def download_imdb_wiki_dataset(path: str = './images/imdb-wiki'):
    """ Downloads the video dataset imdb-wiki and parses a information.csv. A homogeneous format for evaluation.
        Details about the dataset can be found here: https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/.

    Parameters
    ----------
    path: str, default = ./videos/ytcelebrity'
        Path where the videos and information.csv should be saved
    """
    path_exists(path)

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
        'entities': mat['imdb']['name'][0][0][0]
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
        LOGGER.info('Downloading part {}/9'.format(part))
        file = os.path.join(path, 'imdb_' + str(part) + '.tar')
        wget.download(url, file)
        LOGGER.info('Extracting part {}/9'.format(part))
        tar = tarfile.open(file)
        tar.extractall(path)
        tar.close()


def download_youtube_faces_db(path: str = './images/youtube-faces-db'):
    """ Parses a information.csv for the youtube-faces-db dataset. A homogeneous format for evaluation.
        Details about the dataset can be found here: https://www.cs.tau.ac.il/~wolf/ytfaces/.

    !!! Dataset must be downloaded manually from https://www.cs.tau.ac.il/~wolf/ytfaces/.

    Parameters
    ----------
    path: str, default = ./videos/ytcelebrity'
        Path where the videos are located and the information.csv should be saved at.
    """
    path_exists(path)

    videos = []
    entities = []
    for entity in os.listdir(path):
        if entity.startswith('.'):
            continue

        for movie in os.listdir(os.path.join(path, entity)):
            if movie.startswith('.'):
                continue

            for frame in os.listdir(os.path.join(path, entity, movie)):
                if frame.startswith('.'):
                    continue

                videos.append(os.path.join(entity, movie, frame))
                entities.append([entity.replace('_', ' ')])

    information = pd.DataFrame(data={
        'file': videos,
        'entities': entities
    })
    information = information.set_index('file')
    information.to_csv(path + '/information.csv')


def download_wikidata_thumbnails(path: str = './thumbnails', entities: list = None):
    """ Downloads the thumbnails of wikidata and parses them in the following structure:
        <Entity1>
            <Thumbnail1>
            <Thumbnail2>
        <Entity2>
            <Thumbnail1>

    Parameters
    ----------
    path: str, default = './videos/ytcelebrity'
        Path where the thumbnails should be saved at.
    entities: str, default = None
        If not none, downloads only the list of entities. All thumbnails otherwise.
    """
    path_exists(path)

    if entities is not None:
        pass
        # TODO code to download entities from the list
    else:
        pass
        # TODO Download all thumbnails


def download_missing_thumbnails(path: str = './videos/ytcelebrity', loaded_entities: list = None):
    data = pd.read_csv(os.path.join(path, 'information.csv'))

    missing_entities = list(set(data['entities']) - set(loaded_entities))
    if len(missing_entities) != 0:
        LOGGER.info('Missing entities detected: {}'.format(missing_entities))
        download_wikidata_thumbnails('./thumbnails', entities=missing_entities)
    else:
        LOGGER.info('No missing entities found')

    return missing_entities
