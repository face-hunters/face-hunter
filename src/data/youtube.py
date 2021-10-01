from pytube import YouTube
import logging
from src.utils.utils import check_path_exists

LOGGER = logging.getLogger('youtube-downloader')


def download_youtube_videos(txt_path: str = None, path: str = 'data/datasets/youtube') -> list:
    """ Downloads videos from youtube

    Args:
        txt_path (str): Location of a text-file containing line-wise URLs of youtube videos.
        path (str): Path where the videos should be saved.

    Returns:
        video_paths (list): List of paths to the downloaded videos.
    """
    check_path_exists(path)

    video_paths = []
    with open(txt_path) as f:
        for line in f:
            url = line.strip()
            video_paths.append(download_youtube_video(url, path))
    return video_paths


def download_youtube_video(url: str, path: str = 'data/datasets/youtube') -> str:
    """ Downloads a single video from youtube.

    Args:
        url (str): YouTube-link of the video to download.
        path (str): Path where the videos should be saved.

    Returns:
        path (str): Path to the downloaded file.
    """
    youtube = YouTube(url)
    LOGGER.info(f'Starting to download {youtube.title}')
    return youtube.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first().download(path)
