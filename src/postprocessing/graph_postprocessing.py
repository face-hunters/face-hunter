import logging
from datetime import timedelta

LOGGER = logging.getLogger('graph-postprocessing')


def extract_scenes(recognitions: list, timestamps: list):
    assert len(recognitions) == len(timestamps), 'recognitions do not fit timestamps'

    scenes = []
    current_scene = None
    for frame, entities in enumerate(recognitions[:-1], 2):
        if set(entities) != set(recognitions[frame - 1]) and set(entities) != set(recognitions[frame - 2]):
            if current_scene is not None:
                scenes.append(current_scene.set_end(timestamps[frame]))
        if set(entities) == set(recognitions[frame - 1]) and set(entities) == set(recognitions[frame - 2]):
            if current_scene is None or set(current_scene.names[0]) != set(entities):
                current_scene = Scene(entities).set_start(timestamps[frame])
        if current_scene is not None and frame == (len(recognitions)):
            scenes.append(current_scene.set_end(timestamps[frame - 1]))
    return scenes


class Scene(object):

    def __init__(self, names: list):
        self.names = names,
        self.start = None
        self.end = None

    def set_start(self, milliseconds):
        self.start = timedelta(milliseconds=milliseconds),
        return self

    def set_end(self, milliseconds):
        self.end = timedelta(milliseconds=milliseconds),
        return self
