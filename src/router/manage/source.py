import hashlib
import requests

from typing import Union

from src.router.db_api import db_api
from fastapi import Depends
from src.router.auth import get_current_user, User
from pydantic import BaseModel


class Source(BaseModel):
    source_type: str
    method: str
    content: Union[str, None]
    source_id: Union[str, None]


def set_sources(data: Source,
                user: User = Depends(get_current_user)):
    """资源管理"""
    if not user.check_permission(3):
        return {"code": 402, "msg": "无法访问"}

    if data.method == "add":
        if not data.content:
            return {'code': 500, 'msg': "没有获取到内容"}
        if data.source_type == "memes":
            source_id = hashlib.md5(requests.get(data.content).content).hexdigest()
        else:
            source_id = hashlib.md5(data.content.encode("utf-8")).hexdigest()
        code, msg = db_api.add_source(data.source_type, source_id, data.content)
        return {'code': code, 'msg': msg}
    elif data.method == "del":
        if not data.source_id:
            return {'code': 500, 'msg': "id"}
        code, msg = db_api.del_source(data.source_type, data.source_id)
        return {'code': code, 'msg': msg}


def get_sources(source_type: str, count: Union[str, int] = 1, page: int = 1):
    """资源获取"""
    if count == "all":
        code, data, page_count = db_api.get_all_source(source_type, page)

        return {'code': code, 'data': data, "page_count": page_count}
    count = int(count)
    code, source = db_api.get_random_source(source_type, count)
    return {'code': code, 'data': source}
