import time
from datetime import datetime

from src.utils.db import management


async def add_black_list(_id, black_type, black_time, remark=""):
    """
    加黑
    """
    if black_type == "QQ":
        black = management.user_black_list
    else:
        black = management.group_black_list
    today_time_int = int(time.mktime(datetime.now().timetuple())) * 1000
    black.update_one({"_id": _id}, {
        "$set": {
            "block_time": today_time_int + black_time * 1000,
            "remark": remark
        },
        "$inc": {
            "black_num": 1
        }
    }, True)


async def check_black_list(_id, black_type):
    """
    检查是否在黑名单中
    """
    if black_type == "QQ":
        black = management.user_black_list
    else:
        black = management.group_black_list
    today_time_int = int(time.mktime(datetime.now().timetuple())) * 1000
    black_info = black.find_one({
        '_id': _id,
        "block_time": {
            "$gt": today_time_int
        }
    })
    if black_info:
        return True, black_info.get("remark")
    return False, ""
