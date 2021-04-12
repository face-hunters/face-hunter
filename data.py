import logging
import os
import tarfile
import wget
from pytube import YouTube
import pandas as pd

LOGGER = logging.getLogger('d')


def download_youtube_videos(url: str = None, path: str = './videos/youtube'):
    if not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)

    videos = []
    entities = []
    with open(url) as f:
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
        'video': videos,
        'entities': entities
    })
    information = information.set_index('video')
    if os.path.exists(path + '/information.csv'):
        information = pd.read_csv(path + '/information.csv').set_index('video').append(information)
    information.to_csv(path + '/information.csv')


def download_seqamlab_dataset(path: str = './videos/ytcelebrity'):
    if not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)

    url = 'http://seqamlab.com/wp-content/uploads/Data/ytcelebrity.tar'
    file = path + '/ytcelebrity.tar'
    LOGGER.info('Downloading Youtube Celebrities Face Tracking and Recognition Data Set')
    wget.download(url, file)
    LOGGER.info('Extracting ...')
    tar = tarfile.open(file)
    tar.extractall(path)
    tar.close()
    os.remove(path + '/ytcelebrity.tar')

    videos = pd.Series(os.listdir(path))
    information = pd.DataFrame(data={
        'video': videos,
        'entities': videos.apply(lambda x: [' '.join(os.path.splitext(path + '/' + x)[0].split('_')[3:5])])
    })
    information = information.set_index('video')
    information.to_csv(path + '/information.csv')


def download_wikidata_thumbnails(query_csv,path: str = './thumbnails'):
    if not os.path.exists(path):
        LOGGER.info('Creating path {}'.format(path))
        os.makedirs(path)
    df = pd.read_csv(query_csv)
    for i in range(len(df)):
        human_id = df['human'][i]
        name = df['humanLabel'][i]
        thumbnail_url = df['pic'][i]
        if not os.path.exists(path + '/' + human_id + name):
            os.makedirs(path + '/' + human_id + name)
        urllib.request.urlretrieve(thumbnail_url, filename=path + '/' + human_id + name + '/' + str(i) + '.jpg')
