import logging
from datetime import timedelta
import numpy as np

LOGGER = logging.getLogger('graph-postprocessing')


def extract_scenes(recognitions: list, timestamps: list, frame_threshold: int = 3):
    assert len(recognitions) == len(timestamps), 'recognitions do not fit timestamps'

    scenes = []
    current_scene = None
    for frame, entities in enumerate(recognitions):
        if frame - 2 < 0:
            continue

        if current_scene is not None and not np.any([np.all(np.char.equal(np.sort(pred), current_scene.names[0]))
                                                     for pred in recognitions[frame - (frame_threshold - 1):frame + 1]]):
            scenes.append(current_scene.set_end(timestamps[frame]))
            current_scene = None

        if current_scene is None and np.all([np.char.equal(np.sort(pred), np.sort(entities))
                                             for pred in recognitions[frame - (frame_threshold - 1):frame]]):
            current_scene = Scene(entities).set_start(timestamps[frame])

        if current_scene is not None and frame == (len(recognitions) - 1):
            scenes.append(current_scene.set_end(timestamps[frame]))
    return scenes


class Scene(object):

    def __init__(self, names: list):
        self.names = np.sort(names),
        self.start = None
        self.end = None

    def set_names(self, names: list):
        self.names = np.sort(names)

    def set_start(self, milliseconds):
        self.start = timedelta(milliseconds=milliseconds),
        return self

    def set_end(self, milliseconds):
        self.end = timedelta(milliseconds=milliseconds),
        return self

    def __repr__(self):
        return f'<{self.names[0]}>: {self.start[0]}, {self.end[0]}'
