import math
import re
from datetime import datetime
from fastapi import Depends
from typing import Union
from src.router.auth import get_current_user, User

from src.utils.db import logs


async def get_chat_log(page: int = 1,
                       bot_id: int = None,
                       qq: Union[int, str] = None,
                       nickname: str = None,
                       group_id: Union[int, str] = None,
                       group_name: str = None,
                       message: str = None,
                       sort: int = -1,
                       user: User = Depends(get_current_user)):
    """
    获取聊天记录
    """
    if not user.check_permission(5):
        return {"code": 402, "msg": "无法访问"}
    filter = {}
    if bot_id:
        filter.update({"bot_id": bot_id})
    if qq:
        filter.update({"user_id": qq})
    if nickname:
        filter.update({"nickname": {"$regex": nickname}})
    if group_id:
        filter.update({"group_id": group_id})
    if group_name:
        filter.update({"group_name": {"$regex": group_name}})
    if message:
        filter.update({"message": {"$regex": message}})

    sort = list({'sent_time': int(sort)}.items())

    limit = 20
    skip = limit * (int(page) - 1)
    project = {'_id': 0}
    db_name = datetime.now().strftime("chat-log-%Y-%m-%d")
    chat_log_db = logs.db[db_name]
    results = chat_log_db.find(filter=filter,
                               sort=sort,
                               limit=limit,
                               skip=skip,
                               projection=project)
    data = []
    chat_log_count = chat_log_db.count_documents(filter)
    page_count = math.ceil(chat_log_count / limit)
    for result in results:
        if "role" not in result:
            result["role"] = "member"
        result["sent_time"] = result["sent_time"].strftime("%Y-%m-%d %H:%M:%S")

        user_id = result["user_id"]
        group_id = result["group_id"]
        message = result["message"]
        del result["message"]

        message_list = []

        for content in re.split(r'(\[CQ:.+?\])', message):
            is_img = re.findall(r"file=(.+?)\.image", content)
            is_record = re.findall(r"file=(.+?\.amr)", content)
            is_json = re.findall(r"CQ:json,data", content)
            if is_img:
                image_name = f"{group_id}-0-{is_img[0].upper()}"
                url = f"https://gchat.qpic.cn/gchatpic_new/{user_id}/{image_name}/0"
                message_list.append({"type": "img", "content": url})
            elif is_record:
                message_list.append({"type": "text", "content": "[这是一条语音]"})
            elif is_json:
                message_list.append({
                    "type": "text",
                    "content": "[这是一个json卡片]"
                })
            elif content:
                message_list.append({"type": "text", "content": content})
        qlogo = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=1"
        result["message_list"] = message_list
        result["qlogo"] = qlogo
        data.append(result)

    if data:
        return {'code': 200, 'data': data, "page_count": page_count}
    else:
        return {'code': 500, 'msg': "信息获取失败"}
