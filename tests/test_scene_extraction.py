from tests import base_test
from src.postprocessing.graph_postprocessing import extract_scenes, Scene


class TestSceneExtraction(base_test.BaseComponentTest):

    def test_default(self):
        predictions = [['Ali', 'Bo'], ['Ali', 'Bo'], ['Bo', 'Ali'], ['Bo', 'Ali'],
                       ['Bo', 'Ali'], ['Bo'], ['Bo'], ['Bo'], ['Bo']]
        timestamps = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected_scenes = [Scene(['Ali', 'Bo']).set_start(3).set_end(8), Scene(['Bo']).set_start(8).set_end(9)]

        scenes = extract_scenes(predictions, timestamps, frame_threshold=3)

        assert repr(expected_scenes) == repr(scenes)


