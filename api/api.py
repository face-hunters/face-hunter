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

#  todo: from config
BY = 'frame'
FRAME_THRESHOLD = 7
STORAGE_TYPE = 'virtuoso'
MEMORY_PATH = ''
VIRTUOSO_URL = 'http://localhost:8890/sparql-auth'
VIRTUOSO_GRAPH = 'http://localhost:8890/DAV/'
VIRTUOSO_USERNAME = 'dba'
VIRTUOSO_PASSWORD = 'dba'
DBPEDIA_CSV = None
WIKIDATA_CSV = None

THUMBNAIL_LIST = None
THUMBNAILS_PATH = '../data/thumbnails'
IMG_WIDTH = 500
DISTANCE_THRESHOLD = 0.72
ENCODER_NAME = 'Facenet'
LABELS_PATH = '../data/embeddings/labels_facenet.pickle'
EMBEDDINGS_PATH = '../data/embeddings/embeddings_facenet.pickle'
INDEX_PATH = '../data/embeddings/index.bin'

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


@app.route('/api/youtube/<id>', methods=['GET'])
def recognize_youtube_video(id):
    result = api.recognize_youtube_video(id, BY, FRAME_THRESHOLD)
    return jsonify({'success': True, 'result': result})


@app.route('/api/query', methods=['POST'])
def get_videos_by_sparql():
    if request.headers['Content-Type'] == 'application/json':
        query = json.loads(request.data).get('query')
        filters = json.loads(request.data).get('filters').rstrip('\n')
        if filters == '':
            filters = None
        result = api.get_videos_by_sparql(query, filters)
        response = jsonify({'success': True, 'result': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    return jsonify({'success': False, 'result': 'wrong request type'})


@app.route('/api/entity/<entity>', methods=['GET'])
def get_scenes_by_entity(entity):
    result = api.get_videos_by_entity(entity)
    if result is not None:
        result = result[:9]
    response = jsonify({'success': True, 'result': result})
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
