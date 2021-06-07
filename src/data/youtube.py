from pytube import YouTube
import logging
from src.utils.utils import check_path_exists

LOGGER = logging.getLogger('y')


def download_youtube_videos(txt_path: str = None, path: str = 'data/datasets/youtube'):
    """ Downloads videos from youtube.

    Parameters
    ----------
    txt_path: str, default = None
        Location of a text-file containing line-wise URLs of youtube videos.

    path: str, default = data/datasets/youtube
        Path where the videos should be saved.
    """
    check_path_exists(path)

    with open(txt_path) as f:
        for line in f:
            url = line.strip()
            download_youtube_video(url, path)


def download_youtube_video(url: str, path: str = 'data/datasets/youtube'):
    """ Downloads a single video from youtube.

    Parameters
    ----------
    url: str, default = None
        YouTube-link of the video to download

    path: str, default = data/datasets/youtube
        Path where the videos should be saved.
    """
    youtube = YouTube(url)
    LOGGER.info(f'Starting to download {youtube.title}')
    youtube.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first().download(path)
