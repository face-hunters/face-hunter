import logging
from datetime import timedelta
import numpy as np

LOGGER = logging.getLogger('graph-postprocessing')


def extract_scenes(recognitions: list, timestamps: list, frame_threshold: int = 3):
    """ Extract scenes out of frame-wise predictions.

    Args:
        recognitions (list): List of lists containing the frame-wise predictions.
        timestamps (list): List with the corresponding timestamps for the predictions.
        frame_threshold (int): Number of similar/not similar consecutive frames to start/end a scene.

    Returns:
        scenes (list): A number of Scenes.
    """
    assert len(recognitions) == len(timestamps), 'recognitions do not fit timestamps'

    scenes = []
    current_scene = None

    # Preprocess recognitions
    cleaned_recognitions = []
    for index, rec in enumerate(recognitions):
        recognition = []
        for entity in rec:
            if entity != 'unknown':
                recognition.append(entity)
        if len(recognition) == 0:
            recognition.append(str(index))
        cleaned_recognitions.append(recognition)

    # Start scene extraction
    for frame, entities in enumerate(cleaned_recognitions):
        if frame - (frame_threshold - 1) < 0:
            continue

        if current_scene is not None and not np.any(
                [len(pred) == len(current_scene.names[0]) or np.all(np.sort(pred) == current_scene.names[0])
                 for pred in cleaned_recognitions[frame - (frame_threshold - 1):frame + 1]]):
            scenes.append(current_scene.set_end(timestamps[frame - frame_threshold + 1]))
            current_scene = None

        if current_scene is not None and frame == (len(recognitions) - 1):
            scenes.append(current_scene.set_end(timestamps[frame]))

        if np.any([((pred) == 0 or len(pred) != len(entities)) for pred in
                   cleaned_recognitions[frame - (frame_threshold - 1):frame]]):
            continue
        print([np.sort(pred) for pred in cleaned_recognitions[frame - (frame_threshold - 1):frame]])
        print(np.sort(entities))

        if current_scene is None and np.all([np.all(np.sort(pred) == np.sort(entities))
                                             for pred in cleaned_recognitions[frame - (frame_threshold - 1):frame]]):
            current_scene = Scene(entities).set_start(timestamps[frame - frame_threshold + 1])

    return scenes


class Scene(object):
    """ Class that represents a scene with its occurring entities, a start and an ending timestamp. """

    def __init__(self, names: list):
        """
        Args:
            names (list): Names of the occurring entities.
        """
        self.names = np.sort(names),
        self.start = None
        self.end = None

    def set_names(self, names: list):
        """ Set the names of entities in the scene.

        Args:
            names (list): Names of the occurring entities.
        """
        self.names = np.sort(names)

    def set_start(self, milliseconds):
        """ Set the start-timestamp in the scene.

        Args:
            milliseconds (int): Milliseconds that have passed since the beginning of the video.
        """
        self.start = timedelta(milliseconds=milliseconds),
        return self

    def set_end(self, milliseconds):
        """ Set the end-timestamp in the scene.

        Args:
            milliseconds (int): Milliseconds that have passed since the beginning of the video.
        """
        self.end = timedelta(milliseconds=milliseconds),
        return self

    def __repr__(self):
        return f'<{self.names[0]}>: {self.start[0]}, {self.end[0]}'
