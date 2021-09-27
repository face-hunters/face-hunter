import argparse
import logging
from src.hunter import Hunter
from src.utils.utils import get_config
import os

LOGGER = logging.getLogger('cli')

on_rtd = os.environ.get('READTHEDOCS') == 'True'

if on_rtd:
    CONFIG = get_config('../src/utils/config.yaml')
else:
    CONFIG = get_config('../src/utils/config.yaml')


def _search(args):
    """ Starts the download of youtube videos

    Parameters
    ----------
    args.url: str, default = 'data/datasets/youtube/urls.txt'
        Location of a text-file containing line-wise URLs of youtube videos and entities that occur in it.
        Format should be: <url>;<entity1>,<entity2>,..

    args.path: str, default = 'data/datasets/youtube'
        The Location where the videos should be saved at.
    """
    if 'virtuoso' in CONFIG:
        LOGGER.info(Hunter.search(args.entity,
                                  'virtuoso',
                                  virtuoso_url=CONFIG['virtuoso']['sparql-auth'],
                                  virtuoso_graph=CONFIG['virtuoso']['graph'],
                                  virtuoso_username=CONFIG['virtuoso']['user'],
                                  virtuoso_password=CONFIG['virtuoso']['password']))
    else:
        LOGGER.info(Hunter.search(args.entity, 'memory', memory_path=CONFIG['memory']['path']))


def _download_datasets(args):
    """ Starts the download of video datasets

    Parameters
    ----------
    args.dataset: str, default = 'youtube-faces-db'
        The dataset to download and parse. Can be: imdb-wiki, imdb-faces, yt-celebrity or youtube-faces-db.

    args.path: str, default = 'data/datasets/youtube-faces-db'
        The Location where the dataset should be saved at.
    """
    from src.data.datasets import download_seqamlab_dataset
    from src.data.datasets import download_imdb_faces_dataset
    from src.data.datasets import download_youtube_faces_db
    from src.data.datasets import download_imdb_wiki_dataset

    options = {
        'imdb-wiki': download_imdb_wiki_dataset,
        'imdb-faces': download_imdb_faces_dataset,
        'yt-celebrity': download_seqamlab_dataset,
        'youtube-faces-db': download_youtube_faces_db
    }
    options[args.dataset](args.path)


def _download_thumbnails(args):
    """ Starts the download of thumbnails

    Parameters
    ----------
    args.path: str, default = 'data/thumbnails'
        The Location where the thumbnails should be saved at.
    """
    from src.data.knowledge_graphs import download_dbpedia_thumbnails, download_wikidata_thumbnails

    download_wikidata_thumbnails(args.path, download=False)
    download_dbpedia_thumbnails(args.path, download=False)


def _run_detection(args):
    """ Starts the face detection

    Parameters
    ----------
    args.index: str, default = None
        Specifies the name of an existing NMSLIB index if it should be loaded.

    args.save: str, default = None
        Specifies the path where the embeddings should be saved locally if they should be saved.

    args.path: str, default = 'data/datasets/yt-celebrity'
        The Location of videos or images to analyze.

    args.thumbnails: str, default = 'data/thumbnails'
        The location of the thumbnails or an existing NMSLIB index.
    """
    from src.models.evaluation import evaluate_on_dataset

    evaluate_on_dataset(args.path, args.thumbnails, ratio=args.ratio, scene_extraction=args.scene_extraction)


def _link(args):
    """ Allows to link a video to the knowledge graph

    Parameters
    ----------
    args.url: str, default = 'https://www.youtube.com/watch?v=elz1J86AExY'
        The link to the video on YouTube to add.
    """
    from src.hunter import Hunter
    if 'virtuoso' in CONFIG:
        LOGGER.info(Hunter(args.url).link('virtuoso',
                                          virtuoso_url=CONFIG['virtuoso']['sparql-auth'],
                                          virtuoso_graph=CONFIG['virtuoso']['graph'],
                                          virtuoso_username=CONFIG['virtuoso']['user'],
                                          virtuoso_password=CONFIG['virtuoso']['password']))
    else:
        LOGGER.info(Hunter(args.url).link('memory', memory_path=CONFIG['memory']['path']))


def _get_parser():
    """ Sets up a command line interface.

    Returns
    ----------
    parser: ArgumentParser
    """
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument('-v', '--verbose', action='count', default=0)
    logging_args.add_argument('-l', '--logfile')
    parser = argparse.ArgumentParser(description='Face-Hunter Command Line Interface',
                                     parents=[logging_args])
    subparsers = parser.add_subparsers(title='action', help='Action to perform')

    # Parser to download videos from youtube
    search = subparsers.add_parser('search', help='Returns videos in which an entity occurs')
    search.add_argument('--entity', help='Name of the entity', type=str, default=None)
    search.set_defaults(action=_search)

    # Parser to download video datasets
    download_videos = subparsers.add_parser('download_video_dataset',
                                            help='Download test video datasets')
    download_videos.add_argument('--path', help='Path to store the dataset', type=str,
                                 default='data/datasets/youtube-faces-db')
    download_videos.add_argument('--dataset',
                                 help='Options are imdb-wiki, imdb-faces, youtube-faces-db and yt-celebrity',
                                 type=str,
                                 default='youtube-faces-db')
    download_videos.set_defaults(action=_download_datasets)

    # Parser to download thumbnails
    download_thumbnails = subparsers.add_parser('download_thumbnails',
                                                help='Download thumbnails for training')
    download_thumbnails.add_argument('--path', help='Path to save the thumbnails at', type=str,
                                     default='data/thumbnails')
    download_thumbnails.set_defaults(action=_download_thumbnails)

    # Parser to evaluate the face recognition
    run_detection = subparsers.add_parser('run_detection',
                                          help='Run face detection on locally downloaded data')
    run_detection.add_argument('--path', help='Path to the videos', type=str, default='data/datasets/ytcelebrity')
    run_detection.add_argument('--thumbnails', help='Path to the thumbnails', type=str, default='data/thumbnails')
    run_detection.add_argument('--ratio', help='Ratio of entities in the dataset and not', type=float, default=1.0)
    run_detection.add_argument('--scene_extraction', help='Threshold for scene postprocessing. Should be 0 for no '
                                                          'postprocessing', type=int, default=0)
    run_detection.set_defaults(action=_run_detection)

    # Parser to link a video
    link = subparsers.add_parser('link',
                                 help='Link entities of a video to a knowledge graph')
    link.add_argument('--url', help='Link to the youtube video',
                      type=str,
                      default='https://www.youtube.com/watch?v=elz1J86AExY')
    link.set_defaults(action=_link)
    return parser


def _logging_setup(verbosity: int = 1, logfile: str = None):
    """ Sets up a logger.

    Parameters
    ----------
    verbosity: int, default = 1
        Defines the log level. A higher verbosity shows more details.

    logfile: str, default = None
        Location to save the logs.
    """
    logger = logging.getLogger()
    log_level = (2 - verbosity) * 10
    fmt = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    formatter = logging.Formatter(fmt)
    logger.setLevel(log_level)
    logger.propagate = False

    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    else:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logging.getLogger('fh:worker').setLevel(logging.INFO)


def main():
    parser = _get_parser()
    args = parser.parse_args()

    _logging_setup(args.verbose, args.logfile)

    if not hasattr(args, 'action'):
        parser.print_help()
        parser.exit()

    args.action(args)


if __name__ == '__main__':
    main()
