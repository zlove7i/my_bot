# coding: utf-8

from src.utils.db import my_bot
from datetime import datetime
from src.utils.config import config


import requests

client_id = config.baidusdkcore.get("client_id")
client_secret = config.baidusdkcore.get("client_secret")


def content_check(content):
    url = "https://aip.baidubce.com/oauth/2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    req = requests.post(url, data=data)
    access_token = req.json().get("access_token")
    url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"
    data = {
        "access_token": access_token,
        "text": content,
    }
    req = requests.post(url, data=data)
    json_data = req.json()
    result = json_data.get("conclusion") == "合规"
    if not result:
        if json_data.get("data"):
            for data in json_data.get("data"):
                for hits in data.get("hits", []):
                    for word in hits.get("words", []):
                        my_bot.forbidden_word.update_one(
                            {"_id": word},
                            {"$set": {"update_time": datetime.now()}},
                            True
                        )
    return result


if __name__ == "__main__":
    print(content_check(""))
