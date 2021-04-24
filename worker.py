import itertools
import os
from helpers import evaluation_metrics
from hunter import Hunter
import logging
import pandas as pd

LOGGER = logging.getLogger('w')


class Worker(object):
    """
    Worker

    Calculates evaluation metrics on datasets, crawls new videos from youtube and links them.
    The worker class should allow easy parallelization later.

    Parameters
    ----------
    index: str, default = None
        Specifies the name of an existing NMSLIB index if it should be loaded.

    save_path: str, default = None
        Specifies the path where the embeddings should be saved locally if they should be saved.

    thumbnails: str, default = './thumbnails'
        The location of the thumbnails or an existing NMSLIB index.

    Attributes
    ----------

    """
    def __init__(self,
                 index: str = None,
                 thumbnails: str = './thumbnails',
                 save_path: str = None):
        self.index = index
        self.thumbnails = thumbnails
        self.save_path = save_path

    def evaluate_dataset(self, path: str = './videos/ytcelebrity'):
        """ Detects entities in a dataset and calculates evaluation metrics

        Parameters
        ----------
        args.path: str, default = './videos/yt-celebrity'
            The Location of the dataset.
        """
        hunter = Hunter()
        if self.index is not None:
            hunter.fit(self.thumbnails, load_data=True, name=self.index)
        else:
            hunter.fit(self.thumbnails)

        if self.save_path is not None:
            hunter.save(self.save_path, self.index)

        data = pd.read_csv(os.path.join(path, 'information.csv'))
        total_accuracy = 0
        total_recall = 0
        total_precision = 0
        for index, file in data.iterrows():
            y = hunter.predict(os.path.join(path, file['file']))
            accuracy, recall, precision = evaluation_metrics(y,
                                                             list(itertools.repeat(file['entities'], len(y))),
                                                             len(hunter.labels))
            LOGGER.info('Accuracy: {}, Recall: {}, Precision: {}'.format(accuracy, recall, precision))
            total_accuracy += accuracy
            total_recall += recall
            total_precision += precision
        total_accuracy = total_accuracy / len(data)
        total_recall = total_recall / len(data)
        total_precision = total_precision / len(data)
        LOGGER.info('Total Accuracy: {}, Total Recall: {}, Total Precision: {}'. format(total_accuracy,
                                                                                        total_recall,
                                                                                        total_precision))

    def crawl_and_link(self):
        pass
