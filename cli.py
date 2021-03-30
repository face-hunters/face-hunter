import argparse
import logging


def _download_videos(args):
    from data import download_seqamlab_dataset

    download_seqamlab_dataset(args.path)


def _download_thumbnails(args):
    from data import download_wikidata_thumbnails

    download_wikidata_thumbnails(args.path)


def _run_detection(args):
    from worker import Worker

    worker = Worker(args.thumbnails, args.videos)
    worker.run_face_detection()


def _get_parser():
    logging_args = argparse.ArgumentParser(add_help=False)
    logging_args.add_argument('-v', '--verbose', action='count', default=0)
    logging_args.add_argument('-l', '--logfile')
    parser = argparse.ArgumentParser(description='Face-Hunter Command Line Interface',
                                     parents=[logging_args])

    # Parser to download videos
    subparsers = parser.add_subparsers(title='action', help='Action to perform')
    download_videos = subparsers.add_parser('download_videos',
                                            help='Download test video datasets')
    download_videos.add_argument('--path', help='Path to store the videos', type=str, default='./videos')
    download_videos.set_defaults(action=_download_videos)

    # Parser to download thumbnails
    subparsers.add_parser('download_thumbnails',
                          help='Download thumbnails for training')

    # Parser to run the face detection
    run_detection = subparsers.add_parser('run_detection',
                                          help='Run face detection on locally downloaded videos')
    run_detection.add_argument('--videos', help='Path to the videos', type=str, default='./videos')
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

    logging.getLogger('mlb:worker').setLevel(logging.INFO)


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
