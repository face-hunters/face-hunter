import argparse
import logging


def _download_youtube_videos(args):
    from data import download_youtube_videos

    download_youtube_videos(args.url, args.path)


def _download_video_datasets(args):
    from data import download_seqamlab_dataset
    from data import download_imdb_faces_dataset
    from data import download_youtube_faces_db
    from data import download_imdb_wiki_dataset

    options = {
        'imdb-wiki': download_imdb_wiki_dataset,
        'imdb-faces': download_imdb_faces_dataset,
        'yt-celebrity': download_seqamlab_dataset,
        'youtube-faces-db': download_youtube_faces_db
    }
    options[args.dataset](args.path)


def _download_thumbnails(args):
    from data import download_wikidata_thumbnails

    download_wikidata_thumbnails(args.path)


def _run_detection(args):
    from hunter import Hunter

    hunter = Hunter()
    hunter.fit(args.thumbnails)
    hunter.predict(args.videos)


def _get_parser():
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument('-v', '--verbose', action='count', default=0)
    logging_args.add_argument('-l', '--logfile')
    parser = argparse.ArgumentParser(description='Face-Hunter Command Line Interface',
                                     parents=[logging_args])
    subparsers = parser.add_subparsers(title='action', help='Action to perform')

    # Parser to download videos from youtube
    youtube_videos = subparsers.add_parser('youtube',
                                            help='Download videos from youtube')
    youtube_videos.add_argument('--url', help='Video URL', type=str, default='./videos')
    youtube_videos.add_argument('--path', help='Path to store the videos', type=str, default='./videos/youtube')
    youtube_videos.set_defaults(action=_download_youtube_videos)

    # Parser to download video datasets
    download_videos = subparsers.add_parser('download_video_datasets',
                                            help='Download test video datasets')
    download_videos.add_argument('--path', help='Path to store the videos', type=str, default='./images/youtube-faces-db')
    download_videos.add_argument('--dataset',
                                 help='Options are imdb-wiki, imdb-faces, youtube-faces-db and yt-celebrity',
                                 type=str,
                                 default='youtube-faces-db')
    download_videos.set_defaults(action=_download_video_datasets)

    # Parser to download thumbnails
    download_thumbnails = subparsers.add_parser('download_thumbnails',
                          help='Download thumbnails for training')
    download_thumbnails.set_defaults(action=_download_thumbnails)

    # Parser to run the face detection
    run_detection = subparsers.add_parser('run_detection',
                                          help='Run face detection on locally downloaded videos')
    run_detection.add_argument('--videos', help='Path to the videos', type=str, default='./videos/ytcelebrity')
    run_detection.add_argument('--thumbnails', help='Path to the thumbnails', type=str, default='./thumbnails')
    run_detection.set_defaults(action=_run_detection)
    return parser


def _logging_setup(verbosity=1, logfile=None):
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

    if not args.action:
        parser.print_help()
        parser.exit()

    args.action(args)


if __name__ == '__main__':
    main()
