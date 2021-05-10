from pytube import YouTube
import os
import logging
from src.utils.utils import check_path_exists

LOGGER = logging.getLogger('y')


def download_youtube_videos(urls: str = None, path: str = 'data/datasets/youtube'):
    """ Downloads videos from youtube and parses an information.csv. A homogeneous format for evaluation.
        The method allows to create own evaluation datasets.

    Parameters
    ----------
    urls: str, default = None
        Location of a text-file containing line-wise URLs of youtube videos and entities that occur in it.
        Format should be: <url>;<entity1>,<entity2>,..

    path: str, default = data/datasets/youtube
        Path where the videos and information.csv should be saved.
    """
    check_path_exists(path)

    videos = []
    entities = []
    with open(urls) as f:
        for line in f:
            line = line.strip()
            video = line.split(';')
            yt = YouTube(video[0])
            LOGGER.info(f'Starting to download {yt.title}')
            videos.append(f'{yt.title}.mp4')
            entities.append(video[1].split(','))
            yt.streams.filter(progressive=True, file_extension='mp4').order_by(
                'resolution').desc().first().download(path)

    information = pd.DataFrame(data={
        'file': videos,
        'entities': entities
    })
    information = information.set_index('file')
    if os.path.exists(os.path.join(path, 'information.csv')):
        information = pd.read_csv(os.path.join(path, 'information.csv')).set_index('video').append(information)
    information.to_csv(os.path.join(path, 'information.csv'))
