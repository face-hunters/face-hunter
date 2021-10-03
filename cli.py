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
    CONFIG = get_config('src/utils/config.yaml')


def _search(args):
    """ Search in an existing knowledge graph for scenes of an entity.

    Args:
        args.entity (str): Name of the entity to look up.
    """
    if 'virtuoso' in CONFIG:
        LOGGER.info(Hunter.search(args.entity,
                                  'virtuoso',
                                  virtuoso_url=CONFIG['virtuoso']['sparql-auth'],
                                  virtuoso_graph=CONFIG['virtuoso']['graph'],
                                  virtuoso_username=CONFIG['virtuoso']['user'],
                                  virtuoso_password=CONFIG['virtuoso']['password'],
                                  dbpedia_csv=CONFIG['face-recognition'].get('dbpedia'),
                                  wikidata_csv=CONFIG['face-recognition'].get('wikidata')))
    else:
        LOGGER.info(Hunter.search(args.entity,
                                  'memory',
                                  memory_path=CONFIG['memory']['path'],
                                  dbpedia_csv=CONFIG.get['face-recognition'].get('dbpedia'),
                                  wikidata_csv=CONFIG['face-recognition'].get('wikidata')))


def _download_datasets(args):
    """ Download video datasets for the evaluation.

    Args:
        args.dataset (str): Name of the Dataset to download. Should be 'imdb-wiki' for the IMDB-Wiki dataset, 'imdb-faces' for IMDB-Faces, 'yt-celebrity'  for YouTube Celebrities Face Tracking and Recognition Datqset, 'youtube-faces-db' for YouTube Faces Database.
        args.path (str): Location where the dataset should be saved.
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
    """ Download thumbnails from Wikidata and DBpedia.

    Args:
        args.path (str): Location where the thumbnails should be saved.
    """
    from src.data.knowledge_graphs import download_dbpedia_thumbnails, download_wikidata_thumbnails

    download_wikidata_thumbnails(args.path, download=False)
    download_dbpedia_thumbnails(args.path, download=False)


def _run_detection(args):
    """ Run the evaluation of face recognition on a downloaded dataset.

    Args:
        args.path (str): Path to the generated information.csv for a downloaded dataset.
        args.thumbnails (str): Location where the thumbnails are saved.
        args.ratio (float): Parameter specifying how many random thumbnails that are not in the dataset should be learned.
        args.scene_extraction (int): The threshold for the scene extraction postprocessing. Should be 0 for no postprocessing.
    """
    from src.models.evaluation import evaluate_on_dataset

    evaluate_on_dataset(args.path, args.thumbnails, ratio=args.ratio, scene_extraction=args.scene_extraction)


def _link(args):
    """ Recognize entities in a video from YouTube and add the information to a knowledge graph.

    Args:
        args.url (str): Location of the video on YouTube.
    """
    from src.hunter import Hunter
    hunter = Hunter(args.url).fit(
        [],
        CONFIG['face-recognition'].get('thumbnails'),
        CONFIG['face-recognition']['img-width'],
        CONFIG['face-recognition']['encoder'],
        CONFIG['face-recognition'].get('labels'),
        CONFIG['face-recognition'].get('embeddings')
    )
    if 'virtuoso' in CONFIG:
        LOGGER.info(hunter.link('virtuoso',
                                algorithm=CONFIG['face-recognition']['algorithm'],
                                method=CONFIG['face-recognition']['method'],
                                space=CONFIG['face-recognition']['space'],
                                distance_threshold=CONFIG['face-recognition']['distance-threshold'],
                                index_path=CONFIG['face-recognition'].get('index'),
                                k=CONFIG['face-recognition']['k'],
                                virtuoso_url=CONFIG['virtuoso']['sparql-auth'],
                                virtuoso_graph=CONFIG['virtuoso']['graph'],
                                virtuoso_username=CONFIG['virtuoso']['user'],
                                virtuoso_password=CONFIG['virtuoso']['password'],
                                dbpedia_csv=CONFIG['face-recognition'].get('dbpedia'),
                                wikidata_csv=CONFIG['face-recognition'].get('wikidata')))
    else:
        LOGGER.info(hunter.link('memory',
                                algorithm=CONFIG['face-recognition']['algorithm'],
                                method=CONFIG['face-recognition']['method'],
                                space=CONFIG['face-recognition']['space'],
                                distance_threshold=CONFIG['face-recognition']['distance-threshold'],
                                index_path=CONFIG['face-recognition'].get('index'),
                                k=CONFIG['face-recognition']['k'],
                                memory_path=CONFIG['memory']['path'],
                                dbpedia_csv=CONFIG['face-recognition'].get('dbpedia'),
                                wikidata_csv=CONFIG['face-recognition'].get('wikidata')))


def _get_parser():
    """ Sets up a command line interface.

    Args:
        parser (ArgumentParser): Argument parser.
    """
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument('-v', '--verbose', action='count', default=0)
    logging_args.add_argument('-l', '--logfile')
    parser = argparse.ArgumentParser(description='Face-Hunter Command Line Interface',
                                     parents=[logging_args])
    subparsers = parser.add_subparsers(title='action', help='Action to perform')

    # Parser to search for videos with an entity
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
    """ Sets up a logging interface.

    Args:
        verbosity (int): Verbosity level of the logging output.
        logfile (str): Location of a logfile in which the logs can be saved.
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
