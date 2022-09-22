import datetime
import time
from typing import Union

from fastapi import Depends
from pydantic import BaseModel
from src.router.auth import User, get_current_user
from src.router.db_api import db_api


class BlackList(BaseModel):
    action: Union[str, None]
    num_type: Union[str, None]
    number: Union[int, None]
    remark: Union[str, None]
    block_time: Union[int, str, None]


async def get_black_list(user: User = Depends(get_current_user)):
    if not user.check_permission(3):
        return {"code": 402, "msg": "无法访问"}
    result, data = db_api.get_black_list()
    if result:
        return {"code": 200, "data": data}
    else:
        return {"code": 400, "msg": "黑名单获取有点问题"}


async def set_black_list(data: BlackList, user: User = Depends(get_current_user)):
    if not user.check_permission(3):
        return {"code": 402, "msg": "无法访问"}
    action = data.action
    num_type = data.num_type
    number = data.number
    remark = data.remark
    block_time = data.block_time
    if action == "del":
        block_time = int(time.mktime(datetime.datetime.now().timetuple())) * 1000
    elif action == "add":
        if not isinstance(block_time, int):
            block_time = datetime.datetime.strptime(data.block_time, "%Y-%m-%dT%H:%M:%S.%f%z")
            block_time = int(time.mktime(block_time.timetuple())) * 1000
    result, msg = db_api.set_black_list(
        num_type, number, block_time, action, remark
    )
    if result:
        return {"code": 200, "msg": msg}
    else:
        return {"code": 400, "msg": msg}

