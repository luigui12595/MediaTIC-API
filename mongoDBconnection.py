import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import collections
import constants

client = MongoClient('localhost', 27017)
db = client[constants.DB_NAME]


def get_posts(post_query):
    try:
        result_array = []
        results = db.posts.find(post_query, {'_id': False})
        for doc in results:
            dict_test = dict((k.encode('ascii'), v) for (k, v) in doc.items())
            for (k, v) in dict_test.items():
                key = k.encode('ascii')
                if isinstance(v, str):
                    dict_test[key] = v.encode('UTF-8', 'ignore')
                elif isinstance(v, ObjectId):
                    dict_test[key] = str(v)
                else:
                    dict_test[key] = v
            dict_test = collections.OrderedDict(sorted(dict_test.items()))
            result_array.append(dict_test)
        max_keys = 0
        keys_list = []
        for doc in result_array:
            if len(doc) > max_keys:
                max_keys = len(doc)
                keys_list = doc.keys();
        for index, doc in enumerate(result_array):
            for key in keys_list:
                if key not in doc:
                    doc[key] = "N/A"
            result_array[index] = collections.OrderedDict(sorted(doc.items()))
        return result_array
    except Exception as bwe:
        print(bwe)
        return result_array


def get_comment_from(post_id):
    try:
        post_result = db.comments.find({
            "post_id": post_id
        }).sort([("post_position", pymongo.ASCENDING), ("comment_position", pymongo.ASCENDING)])
        results = []
        for doc in post_result:
            del doc["_id"]
            results.append(doc)
        return results
    except Exception as bwe:
        print(bwe)
        return results


def get_comment_by_posts(post_query, comment_query=None):
    try:
        ids_list = list(db.posts.find(post_query, {'_id':0,'post_id':1}).sort([("post_published_unix",pymongo.ASCENDING)]))
        ids_array = []
        for doc in ids_list:
            ids_array.append(doc["post_id"])
        if comment_query is None:
            post_result = db.comments.find({
                 "post_id": {"$in": ids_array}
            }).sort([("post_id", pymongo.ASCENDING),("post_position", pymongo.ASCENDING), ("comment_position", pymongo.ASCENDING)])
        else:
            comment_query["post_id"] = {"$in": ids_array}
            post_result = db.comments.find(
                comment_query
            ).sort(
                [("post_id", pymongo.ASCENDING), ("post_position", pymongo.ASCENDING), ("comment_position", pymongo.ASCENDING)])
        results = list(post_result)
        for post in results:
            del post['_id']
        return results
    except Exception as bwe:
        print(bwe)
        return results


def update_post(post_id, post_data):
    try:
        post_id = ObjectId(post_id)
        del post_data['_id']
        result = db.posts.update_one({'_id': post_id}, {'$set': post_data})
        return result
    except Exception as bwe:
        print(bwe)
        return result


def try_insert_posts(posts_array):
    try:
        bulk = pymongo.bulk.BulkOperationBuilder(db.posts, ordered=True)
        for doc in posts_array:
            bulk.find(doc).upsert().update({
                "$setOnInsert": doc
            })

        response = bulk.execute()
        return response
    except Exception as bwe:
        print(bwe)
        return response


def try_insert_comments(comments_array):
    try:
        bulk = pymongo.bulk.BulkOperationBuilder(db.comments, ordered=True)
        for doc in comments_array:
            if doc["position"] is not None:
                positions = doc["position"].split("_")
                doc["post_position"] = int(positions[0])
                doc["comment_position"] = int(positions[1])
                bulk.find(doc).upsert().update({
                    "$setOnInsert": doc
                })
            else:
                print(doc)
        response = bulk.execute()
        return response
    except Exception as bwe:
        print(bwe)
        return response
