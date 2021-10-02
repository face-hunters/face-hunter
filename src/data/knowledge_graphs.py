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
from src.preprocessing.file_preprocessing import name_norm

LOGGER = logging.getLogger('knowledge-graphs')


def download_wikidata_thumbnails(path: str = 'data/thumbnails/wikidata_thumbnails', query_links: bool = True,
                                 download: bool = True):
    """ Queries the thumbnail links from wikidata and saves the links in a file path/Thumbnails_links.csv
        Downloads the thumbnails of wikidata and parses them in the following structure:
        <Entity1>
        <Thumbnail1>
        <Entity2>
        <Thumbnail1>
        Saves a summary of the results in path/download_results.csv
        Saves the images in path/thumbnails

    Args:
        path (str): Path where the thumbnails should be saved at
        query_links (bool): Boolean that indicates whether to query the thumbnails links
        download (bool): Boolean that indicated whether to download the thumbnails
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
            sparql = SPARQLWrapper('http://query.wikidata.org/sparql')
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            q_results = sparql.query().convert()
            query_results = query_results.append(json_normalize(q_results['results']['bindings']))
        query_results = query_results[['entity.value', 'img.value', 'name.value']]
        query_results = query_results.rename(columns={col: col.split('.')[0] for col in query_results.columns})
        query_results = query_results.drop_duplicates()
        query_results = query_results.reset_index()
        name_list = query_results['name'].tolist()
        norm_name = name_norm(name_list)
        query_results['norm_name'] = norm_name
        tmp_query_results = query_results.drop_duplicates(subset=['entity','norm_name'])
        norm_name = tmp_query_results['norm_name'].tolist()
        folder_name = [v + '_wiki_' + str(norm_name[:i].count(v) + 1) if norm_name.count(v) > 1 else v for i, v in enumerate(norm_name)]
        tmp_query_results['folder_name'] = folder_name
        tmp_query_results = tmp_query_results.drop(['img', 'name', 'index'],axis=1)
        query_results = pd.merge(query_results, tmp_query_results, on = ['entity', 'norm_name'])
        query_results = query_results.drop(query_results[query_results['norm_name'] == 'missing'].index)
        query_results.to_csv(os.path.join(path, f'wikidata_Thumbnails_links.csv'), index=False)
    if download:
        LOGGER.info('Starting to download wikidata thumbnails')
        download_images(path, 'wikidata')


def download_dbpedia_thumbnails(path: str = 'data/thumbnails/dbpedia_thumbnails', query_links: bool = True,
                                download: bool = True):
    """ Queries the thumbnail links from dbpedia and saves the links in a file path/Thumbnails_links.csv
        Downloads the thumbnails of dbpedia and parses them in the following structure:
        <Entity1>
        <Thumbnail1>
        <Entity2>
        <Thumbnail1>
        Saves a summary of the results in path/download_results.csv
        Saves the images in path/thumbnails

    Args:
        path (str): ath where the thumbnails should be saved at
        query_links (bool): Boolean that indicates whether to query the thumbnails links
        download (bool): Boolean that indicated whether to download the thumbnails
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
        OPTIONAL{?entity dbp:name ?name}
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
        name_list = query_results['name'].tolist()
        norm_name = name_norm(name_list)
        query_results['norm_name'] = norm_name
        tmp_query_results = query_results.drop_duplicates(subset=['entity','norm_name'])
        norm_name = tmp_query_results['norm_name'].tolist()
        folder_name = [v + '_db_' + str(norm_name[:i].count(v) + 1) if norm_name.count(v) > 1 else v for i, v in enumerate(norm_name)]
        tmp_query_results['folder_name'] = folder_name
        tmp_query_results = tmp_query_results.drop(['img', 'name', 'index'],axis=1)
        query_results = pd.merge(query_results, tmp_query_results, on = ['entity', 'norm_name'])
        query_results = query_results.drop(query_results[query_results['norm_name'] == 'missing'].index)
        query_results.to_csv(os.path.join(path, f'dbpedia_Thumbnails_links.csv'), index=False)
    if download:
        LOGGER.info('Starting to download dbpedia thumbnails')
        download_images(path, 'dbpedia')


def download_images(path, method='wikidata'):
    """ Downloads entity thumbnails

    Args:
        path (str): Path where the thumbnails should be stored and the Thumbnails_links.csv is located.
        method (str): Source knowledge graph.
    """
    def mycallback(result):
        global results
        results.append(result)

    query_results = pd.read_csv(os.path.join(path, f'{method}_Thumbnails_links.csv'))
    pool = mp.Pool(mp.cpu_count())
    download_list = []
    global results
    results = []
    for i in query_results.index.to_list():
        folder_name = query_results.loc[i, 'folder_name']
        thumbnail_url = query_results.loc[i, 'img']
        i_path = os.path.join(path, 'thumbnails', folder_name)
        file_name = f"{folder_name}_{i}.{thumbnail_url.split('.')[-1]}".split('?width')[0]
        download_list.append([i, thumbnail_url, i_path, file_name])
    for i_entity, thumbnail_url, i_path, file_name in download_list:
        pool.apply_async(download_thumbnail, args=(i_entity, thumbnail_url, i_path, file_name), callback=mycallback)
    pool.close()
    pool.join()
    results = pd.DataFrame(results, columns=["index", "url", "result"])
    results.to_csv(os.path.join(path, 'download_results.csv'), index=False)


def download_thumbnail(index: int, i_thumbnail_url: str, i_path: str, i_file_name: str):
    """ Downloads a single thumbnail

    Args:
        index (int): The index of the downloaded thumbnail taken from the thumbnail urls dataframe
        i_thumbnail_url (str): The url of the downloaded thumbnail
        i_path (str): The download path
        i_file_name (str): The file name

    Returns:
        output (list): A list containing the index, the thumbnail url and the result outcome (success, HTTPError or UnicodeEncodeError)
    """
    try:
        if index % 10 == 0:
            LOGGER.info(f'{index} downloaded')
        check_path_exists(os.path.join(i_path))
        headers = {'user-agent': 'bot'}
        if not os.path.exists(os.path.join(i_path, i_file_name)):
            while True:
                time.sleep(3)
                r = requests.get(i_thumbnail_url, headers=headers)
                with open(os.path.join(i_path, i_file_name), 'wb') as f:
                    f.write(r.content)
                if os.path.getsize(os.path.join(i_path, i_file_name))!=1820:
                    break
                else:
                    LOGGER.info(r)
        else:
            if os.path.getsize(os.path.join(i_path, i_file_name))==1820:
                while True:
                    time.sleep(3)
                    r = requests.get(i_thumbnail_url, headers=headers)
                    with open(os.path.join(i_path, i_file_name), 'wb') as f:
                        f.write(r.content)
                    if os.path.getsize(os.path.join(i_path, i_file_name))!=1820:
                        break
                    else:
                        LOGGER.info(f'{r}:{len(r.content)}')
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


def download_entity_list(path: str = 'data/thumbnails', entity_list: list = None):
    """ Downloads a specific list of entity thumbnails from wikidata.

    Args:
        path (str): Path where the thumbnails are stored.
        entity_list (list): A list of entities required to download
     
    Returns:
        sm (list): A list containing the still missing entities
    """
    url = 'https://query.wikidata.org/sparql'
    sm = []
    query_results = pd.DataFrame()
    for entity in entity_list:
      try:
        query = f'''
        SELECT ?entity ?img ?name
        WHERE
          {{?entity rdfs:label '{entity}'@en;
           wdt:P18 ?img.
           BIND ('{entity}'@en AS ?name)
          }}
        '''
        sparql = SPARQLWrapper('http://query.wikidata.org/sparql')
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        q_results = sparql.query().convert()
        missing_img = json_normalize(q_results['results']['bindings'])
        if missing_img.empty:
            sm.append(entity)
            LOGGER.info(f'{entity} is not found in wikidata as well')
            continue
        query_results = query_results.append(missing_img)
      except:
        sm.append(entity)
        continue
    query_results = query_results[['entity.value', 'img.value', 'name.value']]
    query_results = query_results.rename(columns={col: col.split('.')[0] for col in query_results.columns})
    query_results = query_results.drop_duplicates()
    query_results = query_results.reset_index()
    query_results['norm_name'] = query_results['name']
    query_results['folder_name'] = query_results['name']
    query_results.to_csv(os.path.join(path, f'missing_Thumbnails_links.csv'), index=False)
    LOGGER.info('Starting to download missing thumbnails')
    download_images(path, 'missing')
    LOGGER.info(f'{len(sm)} people are still not found')
    return sm


def download_missing_thumbnails(path: str = './videos/ytcelebrity', path_thumbnails: str = 'data/thumbnails'):
    """ Compares a list of entities with the ones in a dataset and downloads missing ones.

    Args:
        path (str): Path where the information.csv of the dataset is saved.
        path_thumbnails (str): Path where the Thumbnails_links.csv is saved.

    Returns:
        missing_entities (list): List of missing entities that have ben found.
    """
    data = pd.read_csv(os.path.join(path, 'information.csv'))
    thumbnails = pd.read_csv(os.path.join(path_thumbnails, 'wikidata_Thumbnails_links.csv'))

    missing_entities = list(set(data['entities']) - set(thumbnails['norm_name']))
    if len(missing_entities) != 0:
        LOGGER.info('Missing entities detected: {}'.format(missing_entities))
        download_entity_list(path='./thumbnails', entity_list=missing_entities)
    else:
        LOGGER.info('No missing entities found')

    return missing_entities


def get_same_as_link(uri: str) -> str:
    """ Gets the corresponding Wikidata/DBpedia uri for a DBpedia/Wikidata uri.

    Args:
        uri (str): A DBpedia- or Wikidata-URI.

    Returns:
        corresponding_uri (str): The uri of the other knowledge graph.
    """
    if uri.startswith('http://dbpedia'):
        query = ('SELECT DISTINCT ?concept '
                 'WHERE { '
                 f'{uri} owl:sameAs ?concept . '
                 'FILTER (regex(str(?concept), "www.wikidata.org")) '
                 '} '
                 'LIMIT 100')
    else:
        query = ('SELECT DISTINCT ?concept '
                 'WHERE {'
                 f'?concept owl:sameAs <{uri}> . '
                 '} '
                 'LIMIT 100')
    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    q_results = sparql.query().convert()
    try:
        return str(json_normalize(q_results['results']['bindings']).loc[0, 'concept.value'])
    except KeyError:
        LOGGER.info(f'Could not find corresponding link for {uri}')
        return ''


def get_uri_from_label(label: str) -> tuple:
    """ Gets the corresponding Wikidata and DBpedia uri for a label.

    Args:
        label (str): A label.

    Returns:
        dbpedia_uri (str): The uri of the entity in DBpedia.
        wikidata_uri (str): The uri of the entity in Wikidata.
    """
    query = ('SELECT ?entity '
             'WHERE { '
             f'?entity rdfs:label "{label}"@en ; '
             'a dbo:Person . '
             '}')
    sparql_dbpedia = SPARQLWrapper('http://dbpedia.org/sparql')
    sparql_dbpedia.setQuery(query)
    sparql_dbpedia.setReturnFormat(JSON)
    q_results = sparql_dbpedia.query().convert()
    try:
        dbpedia_uri = str(json_normalize(q_results['results']['bindings']).loc[0, 'entity.value'])
    except KeyError:
        LOGGER.info('no dbpedia entry found')
        dbpedia_uri = None

    query = ('SELECT ?entity '
             'WHERE { '
             f'?entity rdfs:label "{label}"@en ; '
             '}')
    sparql_wikidata = SPARQLWrapper('https://query.wikidata.org/sparql')
    sparql_wikidata.setQuery(query)
    sparql_wikidata.setReturnFormat(JSON)
    q_results = sparql_wikidata.query().convert()
    try:
        wikidata_uri = str(json_normalize(q_results['results']['bindings']).loc[0, 'entity.value'])
    except KeyError:
        LOGGER.info('no dbpedia entry found')
        wikidata_uri = None

    return dbpedia_uri, wikidata_uri


def get_uri_from_csv(name: str, data: pd.DataFrame):
    """ Gets the DBpedia- and Wikidata-URI from a Thumbnail_links.csv as a dataframe.

    Args:
        name (str): Name of the entity.
        data (DataFrame): Dataframe of the Thumbnail_links.csv

    Returns:
        dbpedia_uri (str): The uri of the entity in DBpedia.
        wikidata_uri (str): The uri of the entity in Wikidata.
    """
    uris = pd.unique(data[data['name'] == name]['entity'])

    dbpedia_uri = None
    wikidata_uri = None
    for uri in uris:
        if uri.startswith('http://dbpedia'):
            dbpedia_uri = uri
        else:
            wikidata_uri = uri

    return dbpedia_uri, wikidata_uri
