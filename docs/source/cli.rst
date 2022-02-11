Command Line Interface
======================

    Evaluation:

    .. code-block::

        $  python cli.py run_detection --path <path> --thumbnails <path> --ratio 1.0 --scene-extraction 0.0

    Threshold fine-tuning:

    .. code-block::

        $  python cli.py find_threshold --path <path> --samples 5 --model <model>

    Download of thumbnails:

    .. code-block::

        $  python cli.py download_thumbnails --path <path>

    Download of Datasets:

    .. code-block::

        $  python cli.py download_video_datasets --path <path> --dataset <dataset>

    Link a video and entities in the knowledge graph:

    .. code-block::

        $  python cli.py link --url <url>

    Search for videos of an entity

    .. code-block::

        $  python cli.py search --entity <entity>
