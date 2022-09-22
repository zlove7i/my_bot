import json
import datetime
import time
from typing import Union

from fastapi import Depends
from pydantic import BaseModel
from src.router.auth import User, get_current_user
from src.router.db_api import db_api


async def get_team(user: User, team_id=0):
    if not user.check_permission(1):
        return {"code": 402, "msg": "无法访问"}
    code, data = db_api.get_team(int(team_id))
    return {"code": code, "data": data}


async def del_team(user: User, team_id=0):
    if not user.check_permission(1):
        return {"code": 402, "msg": "无法访问"}
    code, data = db_api.get_team(team_id)
    return {"code": code, "data": data}


async def add_team(user: User, team_id=0):
    if not user.check_permission(1):
        return {"code": 402, "msg": "无法访问"}
    code, data = db_api.get_team(team_id)
    return {"code": code, "data": data}


async def set_team(user: User, info):
    if not user.check_permission(1):
        return {"code": 402, "msg": "无法访问"}
    code, data = db_api.set_team(info, user.username)
    return {"code": code, "data": data}


actions = {
    "get": get_team,
    "del": del_team,
    "add": add_team,
    "set": set_team,
}


class Jx3Team(BaseModel):
    action: Union[str, None]
    params: Union[dict, None]


async def jx3_team(data: Jx3Team, user: User = Depends(get_current_user)):
    code = 400
    msg = "好像哪里出错了"
    if data.action not in actions:
        code = 400
        msg = "请求内容不太对"
        return {"code": code, "msg": msg}
    data.params.update({"user": user})
    return await actions[data.action](**data.params)
