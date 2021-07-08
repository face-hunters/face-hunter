import os
import pandas as pd
import requests
import logging
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp
from pandas import json_normalize
from urllib.error import HTTPError
import time
from src.utils.utils import check_path_exists

LOGGER = logging.getLogger('knowledge-graphs')


def download_wikidata_thumbnails(path: str = 'data/thumbnails/wikidata_thumbnails', query_links: bool = True, download: bool = True):
    """ Queries the thumbnail links from wikidata and saves the links in a file path/Thumbnails_links.csv
    Downloads the thumbnails of wikidata and parses them in the following structure:
        <Entity1>
            <Thumbnail1>
        <Entity2>
            <Thumbnail1>
    saves a summary of the results in path/download_results.csv
    saves the images in path/thumbnails
    Parameters
    ----------
    path: str, default = data/thumbnails/wikidata_thumbnails
        Path where the thumbnails should be saved at
    query_links: bool, default = True
        Boolean that indicates whether to query the thumbnails links
    download: bool, default = True
        Boolean that indicated whether to download the thumbnails
    """
    if query_links:
        check_path_exists(path)
        job_list = ['Q82955', 'Q937857', 'Q36180', 'Q33999', 'Q1650915', 'Q1028181', 'Q1930187', 'Q177220', 'Q49757']
        url = 'https://query.wikidata.org/sparql'
        query_results = pd.DataFrame()
        for job in job_list:
            query = f'''
            SELECT ?entity ?img ?name
            WHERE
            {{?entity wdt:P31 wd:Q5 ; 
              wdt:P106 wd:{job} ;
              wdt:P18 ?img  ;
              wdt:P569 ?date .
              FILTER( ?date >= "1940-01-01T00:00:00"^^xsd:dateTime )
              ?entity rdfs:label ?name FILTER (LANG(?name) = "en")
            }}
            '''
            r = requests.get(url, params = {'format': 'json', 'query': query})
            q_results = r.json()
            query_results = query_results.append(json_normalize(q_results['results']['bindings']))
        query_results = query_results[['entity.value', 'img.value', 'name.value']]
        query_results = query_results.rename(columns={col: col.split('.')[0] for col in query_results.columns})
        query_results = query_results.drop_duplicates()
        query_results = query_results.reset_index()
        query_results.to_csv(os.path.join(path, f'Thumbnails_links.csv'), index=False)
    if download:
        LOGGER.info('Starting to download wikidata thumbnails')
        download_images(path)


def download_dbpedia_thumbnails(path: str = 'data/thumbnails/dbpedia_thumbnails', query_links: bool = True, download: bool = True):
    """ Queries the thumbnail links from dbpedia and saves the links in a file path/Thumbnails_links.csv
    Downloads the thumbnails of dbpedia and parses them in the following structure:
        <Entity1>
            <Thumbnail1>
        <Entity2>
            <Thumbnail1>
    saves a summary of the results in path/download_results.csv
    saves the images in path/thumbnails
    Parameters
    ----------
    path: str, default = data/thumbnails/dbpedia_thumbnails
        Path where the thumbnails should be saved at
    query_links: bool, default = True
        Boolean that indicates whether to query the thumbnails links
    download: bool, default = True
        Boolean that indicated whether to download the thumbnails
    """
    check_path_exists(path)
    if query_links:
        LOGGER.info('Starting to query dbpedia thumbnail links')
        query_results = pd.DataFrame()
        query_number = '''
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT (COUNT( ?entity) AS ?count)
        WHERE {
        SELECT ?entity, ?img, ?name
        WHERE {
        ?entity a dbo:Person.
        ?entity dbo:thumbnail ?img.
        OPTIONAL{?entity foaf:name ?name}
        FILTER(LANG(?name) = 'en').
        }}
        '''
        sparql = SPARQLWrapper('http://dbpedia.org/sparql')
        sparql.setQuery(query_number)
        sparql.setReturnFormat(JSON)
        q_results = sparql.query().convert()
        number = json_normalize(q_results['results']['bindings'])
        max_offset = int(number.loc[0, 'count.value'])
        for offset in range(0, max_offset, 10000):
            query = '''
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT ?entity, ?img, ?name
            WHERE {
            SELECT ?entity, ?img, ?name
            WHERE {
            ?entity a dbo:Person.
            ?entity dbo:thumbnail ?img.
            OPTIONAL{?entity foaf:name ?name}
            FILTER(LANG(?name) = 'en').
            }}
            '''
            query = query + f" OFFSET {offset} LIMIT 10000"
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            q_results = sparql.query().convert()
            query_results = query_results.append(json_normalize(q_results['results']['bindings']))
        query_results = query_results[['entity.value', 'img.value', 'name.value']]
        query_results['img.value'] = query_results['img.value'].apply(lambda x: x.split('?')[0])
        query_results = query_results.rename(columns={col: col.split('.')[0] for col in query_results.columns})
        query_results['name'] = query_results.groupby(['entity', 'img']).transform(lambda x: ' / '.join(x))
        query_results = query_results.drop_duplicates()
        query_results = query_results.reset_index()
        query_results.to_csv(os.path.join(path, f'Thumbnails_links.csv'), index=False)
    if download:
        LOGGER.info('Starting to download dbpedia thumbnails')
        download_images(path)


def download_images(path):
    def mycallback(result):
        global results
        results.append(result)

    query_results = pd.read_csv(os.path.join(path, f'Thumbnails_links.csv'))
    pool = mp.Pool(mp.cpu_count())
    download_list = []
    global results
    results = []
    for i in query_results.index.to_list():
        entity_name = query_results.loc[i, 'entity'].split('/')[-1]
        thumbnail_url = query_results.loc[i, 'img']
        i_path = os.path.join(path, 'thumbnails', entity_name)
        file_name = f"{entity_name}{i}.{thumbnail_url.split('.')[-1]}"
        download_list.append([i, thumbnail_url, i_path, file_name])
    for i_entity, thumbnail_url, i_path, file_name in download_list:
        pool.apply_async(download_thumbnail, args=(i_entity, thumbnail_url, i_path, file_name), callback=mycallback)
    pool.close()
    pool.join()
    results = pd.DataFrame(results, columns=["index", "url", "result"])
    results.to_csv(os.path.join(path, 'download_results.csv'), index=False)


def download_thumbnail(index: int, i_thumbnail_url: str, i_path: str, i_file_name: str):
    """ Downloads a thumbnail from dbpedia

    Parameters
    ----------
    index: int
        The index of the downloaded thumbnail taken from the thumbnail urls dataframe
    i_thumbnail_url: str
        The url of the downloaded thumbnail
    i_path: str
        The download path
    i_file_name: str
        The file name

    Returns
    ----------
    output: list
        A list containing the index, the thumbnail url and the result outcome (success, HTTPError or UnicodeEncodeError)
    """
    try:
        if index % 10000 == 0:
            LOGGER.info(f'Downloaded {index} thumbnails')
        time.sleep(0.001)
        check_path_exists(os.path.join(i_path))
        headers = {'user-agent': 'bot'}
        r = requests.get(i_thumbnail_url, headers=headers)
        with open(os.path.join(i_path, i_file_name), 'wb') as f:
            f.write(r.content)
        output = [index, i_thumbnail_url, 'success']
        return output
    except HTTPError:
        os.remove(i_path)
        output = [index, i_thumbnail_url, 'HTTPError']
        return output
    except UnicodeEncodeError:
        os.remove(i_path)
        output = [index, i_thumbnail_url, 'UnicodeEncodeError']
        return output


def download_entity_list(path: str = './thumbnails', entity_list: list = None):
  """ Download a list of entities'thumbnails from wikidata.
  Parameters
  ----------
  path: str, default = './thumbnails'
      Path where the thumbnails are stored.
  entity_list: list, default = None
      a list of entities required to download
  """
  url = 'https://query.wikidata.org/sparql'
  for entity in entity_list:
    query = f'''
    SELECT *
    WHERE
      {{
          ?s rdfs:label '{entity}'@en;
            wdt:P31 wd:Q5;
            wdt:P18 ?img;
      }}
    '''
    r = requests.get(url, params = {'format': 'json', 'query': query})
    q_results = r.json()
    missing_img = json_normalize(q_results['results']['bindings'])
    if missing_img.empty:
      LOGGER.info(f'{entity} is not found in wikidata as well')
      continue
    missing_img = missing_img[['img.value']]
    missing_img = missing_img.rename(columns={col: col.split('.')[0] for col in missing_img.columns})
    for index, row in missing_img.iterrows():
      download_thumbnail(index = index, i_thumbnail_url = row['img'], i_path = os.path.join(path,entity), i_file_name = f'{entity}_{index}')
                           
                                                    
def download_missing_thumbnails(path: str = './videos/ytcelebrity', loaded_entities: list = None):
    """ Compares a list of entities with a dataset and downloads missing ones.
    Parameters
    ----------
    path: str, default = './videos/ytcelebrity'
        Path where the information.csv of the dataset is saved.
    loaded_entities: list, default = None
        Comparable list of entities.
    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))

    missing_entities = list(set(data['entities']) - set(loaded_entities))
    if len(missing_entities) != 0:
        LOGGER.info('Missing entities detected: {}'.format(missing_entities))
        download_entity_list(path = './thumbnails', entity_list = missing_entities)
    else:
        LOGGER.info('No missing entities found')

    return missing_entities
