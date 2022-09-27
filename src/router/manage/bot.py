from src.router.db_api import db_api, management
from fastapi import Depends
from src.router.auth import get_current_user, User
from pydantic import BaseModel
import json
from typing import Union


class ManipulateBot(BaseModel):
    action: Union[str, None]
    data: Union[dict, None]


async def get_bot_list(page: int = 1, filter: str = "{}", user: User = Depends(get_current_user)):
    if not user.check_permission(1):
        return {"code": 402, "msg": "无法访问"}
    data, page_count = db_api.get_bot_list(user, page, json.loads(filter))
    response_data = {
        "code": 200,
        "data": data,
        "page": page,
        "page_count": page_count}
    if user.token:
        response_data["token"] = user.token
    return response_data


async def manipulate_bot(req_data: ManipulateBot, user: User = Depends(get_current_user)):
    actions = {
        "del": del_bot,
        "set_status": set_bot_status,
        "set_info": set_bot_info,
        "set_access_group_num": set_access_group_num,
    }
    code = 400
    msg = "好像哪里出错了"

    if req_data.action not in actions:
        code = 400
        msg = "请求内容不太对"
        return {"code": code, "msg": msg}
    req_data.data["user"] = user
    result = await actions[req_data.action](**req_data.data)
    return result


async def set_bot_status(bot_id: int, user: User):
    if not user.check_permission(3):
        if not db_api.check_master(user.username, bot_id):
            return {"code": 402, "msg": "无法访问"}
    bot_info = management.bot_info.find_one({"_id": bot_id})
    work_stat = False
    if bot_info:
        work_stat = not bot_info.get("work_stat")
    if db_api.set_bot(bot_id, {"work_stat": work_stat}):
        return {"code": 200, "msg": f"{bot_id}修改状态成功"}
    else:
        return {"code": 400, "msg": f"{bot_id}修改状态失败"}


async def set_bot_info(bot_id, user: User, enable=False, master=None):
    if not user.check_permission(3):
        if not db_api.check_master(user.username, bot_id):
            return {"code": 402, "msg": "无法访问"}
    if db_api.set_bot(bot_id, {"enable": enable, "master": master}):
        return {"code": 200, "msg": f"{bot_id}修改状态成功"}
    else:
        return {"code": 400, "msg": f"{bot_id}修改状态失败"}


async def del_bot(bot_id: int, user: User):
    if not user.check_permission(3):
        if not db_api.check_master(user.username, bot_id):
            return {"code": 402, "msg": "无法访问"}
    if db_api.del_bot(bot_id):
        return {"code": 200, "msg": f"删除{bot_id}成功"}
    else:
        return {"code": 400, "msg": f"删除{bot_id}失败"}


async def set_access_group_num(bot_id: int, access_group_num: int, user: User):
    if not user.check_permission(3):
        if not db_api.check_master(user.username, bot_id):
            return {"code": 402, "msg": "无法访问"}
    if not management.bot_info.find_one({"_id": bot_id}):
        return {"code": 400, "msg": f"{bot_id}不存在"}
    management.bot_info.update_one(
        {"_id": bot_id}, {"$set": {
            "access_group_num": access_group_num
        }}, True)
    return {"code": 200, "msg": f"修改{bot_id}加群上限成功"}
