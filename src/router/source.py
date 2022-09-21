import hashlib
import json
import requests

from flask import jsonify, request
from flask.views import MethodView
from src.utils.auth import constant, login_required
from src.utils.db import db_api


class Meme(MethodView):
    @login_required(constant.PERMISSION_LEVEL_3)
    def post(self):
        """管理表情"""
        data = request.get_data()
        data = json.loads(data.decode("UTF-8"))
        if data.get("method") == "add":
            meme_url = data.get("meme_url")
            if not meme_url:
                return jsonify({'code': 500, 'msg': "没有获取到表情链接"})
            meme_id = hashlib.md5(requests.get(meme_url).content).hexdigest()
            code, msg = db_api.add_meme(meme_id, meme_url)
            return jsonify({'code': code, 'msg': msg})
        elif data.get("method") == "del":
            meme_id = data.get("meme_id")
            if not meme_id:
                return jsonify({'code': 500, 'msg': "没有获取到表情id"})
            code, msg = db_api.del_meme(meme_id)
            return jsonify({'code': code, 'msg': msg})

    def get(self):
        data = dict(request.args)
        if data.get("method") == "random":
            code, memes = db_api.get_random_meme(int(data.get("count", 1)))
            return jsonify({'code': code, 'memes': memes})
        page = 1
        if data.get("page"):
            page = int(data.get("page"))
            code, data, page_count = db_api.get_meme(page)

            return jsonify({'code': code, 'data': data, "page_count": page_count})
        return jsonify({'code': 500, 'data': "你的请求写错了吧"})

class KFC(MethodView):
    @login_required(constant.PERMISSION_LEVEL_3)
    def post(self):
        """管理疯狂星期四"""
        data = request.get_data()
        data = json.loads(data.decode("UTF-8"))
        if data.get("method") == "add":
            kfc_content = data.get("content")
            if not kfc_content:
                return jsonify({'code': 500, 'msg': "没有获取到文案"})
            code, msg = db_api.add_kfc(kfc_content)
            return jsonify({'code': code, 'msg': msg})
        elif data.get("method") == "del":
            kfc_id = data.get("kfc_id")
            if not kfc_id:
                return jsonify({'code': 500, 'msg': "没有获取到文案id"})
            code, msg = db_api.del_kfc(kfc_id)
            return jsonify({'code': code, 'msg': msg})

    def get(self):
        data = dict(request.args)
        if data.get("method") == "random":
            code, content = db_api.get_random_kfc(int(data.get("count", 1)))
            return jsonify({'code': code, 'content': content})
        page = 1
        if data.get("page"):
            page = int(data.get("page"))
            code, data, page_count = db_api.get_kfc(page)

            return jsonify({'code': code, 'data': data, "page_count": page_count})
        return jsonify({'code': 500, 'data': "你的请求写错了吧"})

class Food(MethodView):
    @login_required(constant.PERMISSION_LEVEL_3)
    def post(self):
        """吃什么"""
        data = request.get_data()
        data = json.loads(data.decode("UTF-8"))
        if data.get("method") == "add":
            content = data.get("content")
            if not content:
                return jsonify({'code': 500, 'msg': "没有获取到食物"})
            code, msg = db_api.add_food(content)
            return jsonify({'code': code, 'msg': msg})
        elif data.get("method") == "del":
            food_id = data.get("food_id")
            if not food_id:
                return jsonify({'code': 500, 'msg': "没有获取到食物id"})
            code, msg = db_api.del_food(food_id)
            return jsonify({'code': code, 'msg': msg})

    def get(self):
        data = dict(request.args)
        if data.get("method") == "random":
            code, content = db_api.get_random_food(int(data.get("count", 1)))
            return jsonify({'code': code, 'content': content})
        page = 1
        if data.get("page"):
            page = int(data.get("page"))
            code, data, page_count = db_api.get_food(page)

            return jsonify({'code': code, 'data': data, "page_count": page_count})
        return jsonify({'code': 500, 'data': "你的请求写错了吧"})
