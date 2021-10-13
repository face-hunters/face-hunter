from tests import base_test
from src.postprocessing.graph_postprocessing import extract_scenes, Scene

PREDICTIONS = [['Ali', 'Bo'], ['Ali', 'Bo'], ['Bo', 'Ali'], ['Bo', 'Ali'],
               ['Bo', 'Ali'], ['Bo'], ['Bo'], ['Bo'], ['Bo']]
TIMESTAMPS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

PREDICTIONS_2 = [['Ali', 'Bo'], ['Ali', 'Bo'], ['Bo', 'Ali'], ['Bo', 'Ali'],
               ['Bo', 'Ali'], ['Bo'], ['Bo'], ['Bo', 'Ali'], ['Bo', 'Ali']]


class TestSceneExtraction(base_test.BaseComponentTest):

    def test_default(self):
        expected_scenes = [Scene(['Ali', 'Bo']).set_start(1).set_end(6), Scene(['Bo']).set_start(6).set_end(9)]

        scenes = extract_scenes(PREDICTIONS, TIMESTAMPS)

        assert repr(expected_scenes) == repr(scenes)

    def test_one_threshold(self):
        expected_scenes = [Scene(['Ali', 'Bo']).set_start(1).set_end(6), Scene(['Bo']).set_start(6).set_end(9)]

        scenes = extract_scenes(PREDICTIONS, TIMESTAMPS, frame_threshold=1)

        assert repr(expected_scenes) == repr(scenes)

    def test_five_threshold(self):
        expected_scenes = [Scene(['Ali', 'Bo']).set_start(1).set_end(9)]

        scenes = extract_scenes(PREDICTIONS, TIMESTAMPS, frame_threshold=5)

        assert repr(expected_scenes) == repr(scenes)

    def test_three_threshold_with_false_predictions(self):
        expected_scenes = [Scene(['Ali', 'Bo']).set_start(1).set_end(9)]

        scenes = extract_scenes(PREDICTIONS_2, TIMESTAMPS, frame_threshold=3)

        assert repr(expected_scenes) == repr(scenes)
