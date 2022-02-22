import os
os.environ['FLASK_running'] = "True"

from flask import (
    Flask,
    jsonify,
    request,
    make_response
)
import json
from flask_ngrok import run_with_ngrok
from flask_api import FlaskApi
from flask_cors import CORS
import threading
from src.utils.utils import get_config


CONFIG = get_config('../src/utils/config.yaml')


BY = CONFIG['face-recognition']['by']
FRAME_THRESHOLD = CONFIG['face-recognition']['postprocessing-threshold']
if 'virtuoso' in CONFIG:
    STORAGE_TYPE = 'virtuoso'
    MEMORY_PATH = ''
    VIRTUOSO_URL = CONFIG['virtuoso']['sparql-auth']
    VIRTUOSO_GRAPH = CONFIG['virtuoso']['graph']
    VIRTUOSO_USERNAME = CONFIG['virtuoso']['user']
    VIRTUOSO_PASSWORD = CONFIG['virtuoso']['password']
else:
    STORAGE_TYPE = 'memory'
    MEMORY_PATH = '../' + CONFIG['memory']['path']
    VIRTUOSO_URL = ''
    VIRTUOSO_GRAPH = ''
    VIRTUOSO_USERNAME = ''
    VIRTUOSO_PASSWORD = ''

DBPEDIA_CSV = CONFIG['face-recognition'].get('dbpedia')
WIKIDATA_CSV = CONFIG['face-recognition'].get('wikidata')

THUMBNAIL_LIST = None
THUMBNAILS_PATH = '../' + CONFIG['face-recognition']['thumbnails']
IMG_WIDTH = CONFIG['face-recognition']['img-width']
DISTANCE_THRESHOLD = CONFIG['face-recognition']['distance-threshold']
ENCODER_NAME = CONFIG['face-recognition']['encoder']
LABELS_PATH = '../' + CONFIG['face-recognition']['labels']
EMBEDDINGS_PATH = '../' + CONFIG['face-recognition']['embeddings']
INDEX_PATH = '../' + CONFIG['face-recognition']['index']

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
run_with_ngrok(app)

api = FlaskApi(
    STORAGE_TYPE,
    MEMORY_PATH,
    VIRTUOSO_URL,
    VIRTUOSO_GRAPH,
    VIRTUOSO_USERNAME,
    VIRTUOSO_PASSWORD,
    DBPEDIA_CSV,
    WIKIDATA_CSV,
    THUMBNAIL_LIST,
    THUMBNAILS_PATH,
    IMG_WIDTH,
    DISTANCE_THRESHOLD,
    ENCODER_NAME,
    LABELS_PATH,
    EMBEDDINGS_PATH,
    INDEX_PATH
)


@app.route('/api/youtube/<youtube_id>', methods=['GET'])
def recognize_youtube_video(youtube_id):
    th = threading.Thread(target=api.recognize_youtube_video, args=(youtube_id, BY, FRAME_THRESHOLD))
    th.start()
    return jsonify({'success': True})


@app.route('/api/query', methods=['POST'])
def get_videos_by_sparql():
    if request.headers['Content-Type'] == 'application/json':
        query = json.loads(request.data).get('query')
        filters = json.loads(request.data).get('filters').rstrip('\n')
        if filters == '':
            filters = None
        result = api.get_videos_by_sparql(query, filters)
        length = 0
        if result is not None:
            length = len(result)
            result = result
        response = jsonify({'success': True, 'result': result, 'length': length})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    return jsonify({'success': False, 'result': 'wrong request type'})


@app.route('/api/entity/<entity>', methods=['GET'])
def get_scenes_by_entity(entity):
    result = api.get_videos_by_entity(entity)
    length = 0
    if result is not None:
        length = len(result)
        result = result
    response = jsonify({'success': True, 'result': result, 'length': length})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def iternal_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)


if __name__ == '__main__':

    app.run()
