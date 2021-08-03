import logging
import wikipedia

LOGGER = logging.getLogger('file-preprocessing')


def name_norm(name_list):
    """ Normalize name based on Wikipedia search

    Parameters
    ----------
    folder: list, default = None
        The name list needs to be normalized

    Returns
    ----------
    list
        The name list has been normalized
    """
    wiki_name = []
    i = 0
    try:
        for name in name_list:
            wikipedia.set_lang("en")
            search_list = wikipedia.search(name, results=1)
            if search_list:
                wiki_name.append(search_list[0])
            else:
                wikipedia.set_lang("de")
                search_list = wikipedia.search(name, results=1)
                if search_list:
                    wiki_name.append(search_list[0])
                else:
                    i = i + 1
                    wiki_name.append('missing')
    except:
        LOGGER.info(f'{name} error')
        wiki_name.append('missing')
    LOGGER.info(f'{i} people cant be found in wikipedia')
    return wiki_name