from flask import Blueprint, send_file, Response, Flask
from contourGenerator import generate_event_contours
main = Blueprint('main', __name__)

import json


@main.route("/ratings/top/", methods=["GET"])
def top_ratings():
    #logger.debug("User %s TOP ratings requested", user_id)
    #top_ratings = {'a':1, 'b':2}
    #return jsonify(top_ratings)
    data = {
        'hello'  : 'world',
        'number' : 3
    }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')
    #resp.headers['Link'] = 'http://luisrei.com'

    return resp

@main.route('/get_image/<events>', methods=["GET"])
def get_image(events):
    eventList = events.split('|')
    generate_event_contours(sc, eventList, stationMagnitudes)
    return send_file("contour.png", mimetype='image/png')


@main.route('/tester/<eventList>')
def test(eventList):
    return str(eventList)

def create_app(spark_context, stationMagList):
    global stationMagnitudes
    global sc
    sc = spark_context
    #recommendation_engine = RecommendationEngine(spark_context, dataset_path)
    stationMagnitudes = stationMagList

    app = Flask(__name__)
    app.register_blueprint(main)
    return app


