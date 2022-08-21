# coding: utf-8

from src.utils.db import db
from datetime import datetime
from src.utils.config import config
# from huaweicloudsdkcore.auth.credentials import BasicCredentials
# from huaweicloudsdkmoderation.v2.region.moderation_region import ModerationRegion
# from huaweicloudsdkcore.exceptions import exceptions
# from huaweicloudsdkmoderation.v2 import *
# import re

# default_categories = [
#     "politics", "porn", "ad", "abuse", "contraband", "flood", "emz_black_list"
# ]

# ak = config.huaweicloudsdkcore.get("ak")
# sk = config.huaweicloudsdkcore.get("sk")
# region = config.huaweicloudsdkcore.get("region")


# def content_check(content, categories=default_categories):
#     if re.match(
#             "(\w+\.)+[com|cn|net|xyz|org|gov|mil|edu|biz|info|pro|name|coop|travel|xxx|idv|aero|museum|mobi|asia|tel|int|post|jobs|cat]",
#             content):
#         return False, None
#     credentials = BasicCredentials(ak, sk)

#     client = ModerationClient.new_builder() \
#         .with_credentials(credentials) \
#         .with_region(ModerationRegion.value_of(region)) \
#         .build()

#     try:
#         request = RunTextModerationRequest()
#         listTextDetectionItemsReqItemsbody = [
#             TextDetectionItemsReq(text=content, type="content")
#         ]
#         request.body = TextDetectionReq(
#             items=listTextDetectionItemsReqItemsbody, categories=categories)
#         response = client.run_text_moderation(request)
#         if response.result.suggestion == "pass":
#             return True, None
#         return False, response.result.detail
#     except exceptions.ClientRequestException as e:
#         print(e.status_code)
#         print(e.request_id)
#         print(e.error_code)
#         print(e.error_msg)

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
                        db.forbidden_word.update_one(
                            {"_id": word},
                            {"$set": {"update_time": datetime.now()}},
                            True
                        )
    return result


if __name__ == "__main__":
    print(content_check(""))
