import logging
import os
import tarfile
import wget

LOGGER = logging.getLogger('d')


def download_seqamlab_dataset(path: str = './videos'):
    if not os.path.exists(path):
        LOGGER.info('Creating path ' + path)
        os.makedirs(path)

    url = 'http://seqamlab.com/wp-content/uploads/Data/ytcelebrity.tar'
    file = path + '/ytcelebrity.tar'
    LOGGER.info('Downloading Youtube Celebrities Data Set')
    wget.download(url, file)
    LOGGER.info('Extracting ...')
    tar = tarfile.open(file)
    tar.extractall(path=path)
    tar.close()
    os.remove(path + '/ytcelebrity.tar')


def download_wikidata_thumbnails(path: str = './thumbnails'):
    if not os.path.exists(path):
        os.makedirs(path)

    # TODO thumbnail download code
