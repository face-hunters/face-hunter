import logging
import wikipedia

LOGGER = logging.getLogger('file-preprocessing')

def norm(name, j):
  LOGGER.info(f'process{j} running')
  try:
    wikipedia.set_lang("en") 
    search_list = wikipedia.search(name, results=1)
    if search_list:
      return (search_list[0],j,1)
    else:
      wikipedia.set_lang("de")
      search_list = wikipedia.search(name, results=1)
      if search_list:
        return (search_list[0],j,1)
      else:
        return (name,j,0)
  except:
    LOGGER.info(f'{name} error')
    return (name,j,0)


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
    def add_name(result):
      global wiki_name
      global missing_name 
      name,j,search = result
      wiki_name[j]=name
      if not search:
        missing_name.append(name)
    global wiki_name
    wiki_name = [None]*len(name_list)
    global missing_name
    missing_name = []
    j = 0
    pool = mp.Pool(mp.cpu_count())
    for name in name_list:
      pool.apply_async(norm, args=(name, j), callback=add_name)
      j = j + 1
    pool.close()
    pool.join()
    LOGGER.info(f'{len(missing_name)} people cant be found in wikipedia, They are:')
    LOGGER.info(missing_name)
    return wiki_name
