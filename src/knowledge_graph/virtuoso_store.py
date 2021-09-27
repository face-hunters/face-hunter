import logging

from SPARQLWrapper import SPARQLWrapper, JSON, DIGEST, POST
from pandas import json_normalize

LOGGER = logging.getLogger('virtuoso-store')


class VirtuosoStore(object):
    """
    Virtuoso Store

    Implementation to store and query rdf-triples in a Virtuoso instance

    """
    def __init__(self, conn_url: str = 'http://localhost:8890/sparql-auth',
                 graph: str = 'http://localhost:8890/DAV/',
                 username: str = 'dba',
                 password: str = 'dba'):
        self.graph = graph
        self.endpoint = SPARQLWrapper(conn_url)
        self.endpoint.setHTTPAuth(DIGEST)
        self.endpoint.setCredentials(username, password)
        self.endpoint.setReturnFormat(JSON)
        self.insert_query = ''

    def insert(self, triple: tuple):
        """ Add a triple to the knowledge graph

        Parameters
        ----------
        triple: tuple
            The triple to save.
        """
        self.insert_query += f' <{str(triple[0])}> <{str(triple[1])}>'
        if type(triple[2]).__name__ == 'Literal':
            self.insert_query += f' "{str(triple[2])}" .'
        else:
            self.insert_query += f' <{str(triple[2])}> .'

    def commit(self):
        """ Make the changes persistent and available
        """
        self.endpoint.setMethod(POST)
        query = ('INSERT DATA {'
                 f'GRAPH <{self.graph}>'
                 ' {'
                 f'{self.insert_query}'
                 '}'
                 '}')
        self.query(query)

    def query(self, query: str):
        """ Execute a SPARQL query against a Virtuoso endpoint

        Parameters
        ----------
        query: str
            A valid SPARQL query.

        Returns
        ----------
        results: List
            Returns a list of lists with the queried properties. Format: [[<property1>, <property2>, ...], ...]
        """
        self.endpoint.setQuery(query)
        query_results = json_normalize(self.endpoint.query().convert()['results']['bindings'])
        value_columns = [col for col in query_results if col.endswith('.value')]
        results = []
        for index, row in query_results.iterrows():
            results.append([row[col] for col in value_columns])
        return results

    def exists(self, youtube_id):
        query = ('SELECT count(?video)'
                 'WHERE {'
                 '?video a mpeg7:Video ;'
                 f'dc:identifier "http://www.youtube.com/watch?v={youtube_id}" .'
                 '} group by ?video')
        return True if int(self.query(query)[0][0]) > 0 else False
