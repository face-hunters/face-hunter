from tests import base_test
from models.evaluation import get_evaluation_metrics
import numpy as np


class TestEvaluation(base_test.BaseComponentTest):

    def test_metric_calculation(self):
        y_pred = [['Sandler'], ['Sandler']]
        y_true = [['Sandler'], ['Bullock']]
        expected_metrics = [0.5, 0.5, 0.5, 0.5]

        metrics = get_evaluation_metrics(y_pred, y_true)

        assert np.all(np.equal(expected_metrics, metrics))

    def test_metric_calculation_image(self):
        y_pred = [['Sandler']]
        y_true = [['Sandler']]
        expected_metrics = [1., 1., 1., 1.]

        metrics = get_evaluation_metrics(y_pred, y_true)

        assert np.all(np.equal(expected_metrics, metrics))

    def test_metric_calculation_multiple_entities(self):
        y_pred = [['Sandler', 'Bullock'], ['Sandler', 'Bullock'], ['Sandler', 'Bullock']]
        y_true = [['Sandler'], ['Sandler', 'Bullock'], ['Sandler', 'Aniston']]
        expected_metrics = [0.61111111, 0.83333333, 0.66666667, 0.72222222]

        metrics = get_evaluation_metrics(y_pred, y_true)

        assert np.allclose(expected_metrics, metrics)

    def test_nothing_equal(self):
        y_pred = [['Sandler']]
        y_true = [['Bullock']]
        expected_metrics = [0., 0., 0., 0.]

        metrics = get_evaluation_metrics(y_pred, y_true)

        assert np.all(np.equal(expected_metrics, metrics))
