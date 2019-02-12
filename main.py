import mongoDBconnection as db
import json
from flask import json
from flask_cors import CORS, cross_origin
from flask import Flask, request
import constants


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)


@app.route(constants.GET_POSTS)
def get_posts():
    params = request.args
    req_params_keys = params.keys()
    db_query_params = {'post_published_unix': {}}
    for param in req_params_keys:
        if param == 'finicio' or param == 'ffinal':
            if param == 'finicio':
                db_query_params["post_published_unix"]["$gte"] = int(params[param])
            if param == 'ffinal':
                db_query_params["post_published_unix"]["$lte"] = int(params[param])
        elif param == 'text':
            db_query_params["$text"] = {}
            db_query_params["$text"]["$search"] = '\"' + params[param] + '\"'
        else:
            key_param = get_attribute_key(param)
            if key_param is not None:
                db_query_params[key_param] = params[param]
    if not bool(db_query_params['post_published_unix']):
        del db_query_params['post_published_unix'];
    results = db.get_posts(db_query_params)
    response = app.response_class(
        response=json.dumps(results),
        status=200,
        mimetype='application/json'
    )
    return response


def get_attribute_key(x):
    return {
        'medio': 'from.facebook_id',
        'tema': 'category',
        'interes': 'interest',
        'campana': 'campaign',
        'tono': 'framing',
        'formato':'format',
        'seccion':'section',
        'periodista':'journalist',
    }.get(x, None)


@app.route(constants.GET_COMMENTS)
def get_comments():
    post_id = request.args.get('post_id', None)
    posts = request.args.get('posts', None)
    search_text_by_post = False
    if posts is not None:
        search_text_by_post = True if posts.lower() == 'true' else False
    if post_id is not None:
        results = db.get_comment_from(post_id)
    else:
        params = request.args
        req_params_keys = params.keys()
        posts_query_params = {'post_published_unix': {}}
        comments_query_params = {}
        for param in req_params_keys:
            if param == 'finicio' or param == 'ffinal':
                if param == 'finicio':
                    posts_query_params["post_published_unix"]["$gte"] = int(params[param])
                if param == 'ffinal':
                    posts_query_params["post_published_unix"]["$lte"] = int(params[param])
            elif param == 'text':
                if search_text_by_post:
                    posts_query_params["$text"] = {}
                    posts_query_params["$text"]["$search"] = params[param]
                    del comments_query_params
                else:
                    comments_query_params["$text"] = {}
                    comments_query_params["$text"]["$search"] = params[param]
            else:
                key = get_attribute_key(param)
                if key is not None:
                    posts_query_params[key] = params[param]
        if not bool(posts_query_params['post_published_unix']):
            del posts_query_params['post_published_unix']
        if search_text_by_post:
            results = db.get_comment_by_posts(posts_query_params)
        else:
            results = db.get_comment_by_posts(posts_query_params, comments_query_params)
    response = app.response_class(
        response=json.dumps(results),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route(constants.UPDATE_POSTS, methods=['PUT'])
def update_post():
    news = json.loads(request.data)
    result = db.update_post(news['post_id'], news)
    response_obj = {"matched": result.matched_count, "modified": result.modified_count}
    response = app.response_class(
        response=json.dumps(response_obj),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route(constants.INSERT_POSTS, methods=['POST'])
def insert_posts():
        json_acceptable_string = request.data.replace("'", "\"")
        posts = json.loads(json_acceptable_string)
        i = 0
        while i < len(posts["dataArray"]):
            print(posts["dataArray"][i])
            if posts["dataArray"][i]['type'] is None:
                del posts["dataArray"][i]
            i += 1
        result = db.try_insert_posts(posts['dataArray'])
        del result['upserted']
        response = app.response_class(
            response=json.dumps(result),
            status=200,
            mimetype='application/json'
        )
        return response


@app.route(constants.INSERT_COMMENTS, methods=['POST'])
def insert_comments():
    json_acceptable_string = request.data
    comments = json.loads(json_acceptable_string)
    result = db.try_insert_comments(comments['dataArray'])
    del result['upserted']
    response = app.response_class(
        response=json.dumps(result),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == '__main__':
    app.run(host=constants.HOST, port=constants.PORT, debug=constants.DEBUG)




