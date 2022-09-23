import hashlib

from pymongo import DeleteOne, MongoClient, UpdateOne

from src.utils.config import config

mg_list = config.mongodb.get("mongdb_list")
mg_usr = config.mongodb.get("mongodb_username")
mg_pwd = config.mongodb.get("mongodb_password")


client = MongoClient(f'mongodb://{",".join(mg_list)}/', username=mg_usr, password=mg_pwd)


def v_0_0_0():
    # 1. 移动表
    l = [
            ("bot_info", "management", "bot_info"),
            ("group_conf", "management", "group_conf"),
            ("pk_log", "logs", "pk_log"),
            ("j3_teams", "jx3_data", "j3_teams"),
            ("tickets", "jx3_data", "tickets"),
            ("jianghu", "jianghu", "user"),
            ("knapsack", "jianghu", "knapsack"),
            ("equip", "jianghu", "equip"),
            ("auction_house", "jianghu", "auction_house"),
            ("npc", "jianghu", "npc")
        ]
    for old_table_name, database_name, new_table_name in l:
        if client["my_bot"][old_table_name].count_documents({}):
            data = client["my_bot"][old_table_name].find()
            client[database_name][new_table_name].insert_many(data)
        client["my_bot"][old_table_name].drop()

    # 2. 转移部分数据
    j3_update_list = []
    jianghu_update_list = []
    for i in client["my_bot"]["user_info"].find():
        jianghu_update_list.append(
            UpdateOne(
                {"_id": i["_id"]},
                {"$set": {
                    "银两": i.get("gold", 100000),
                    "精力": i.get("energy", 100),
                    "是否签到": i.get("is_sign", False),
                    "秘境次数": i.get("dungeon_num", 0),
                    "贡献": i.get("contribution", 0),
                    "丢弃装备次数": i.get("discard_equipment_num", 0),
                    "签到时间": i.get("last_sign")
                }}
            )
        )
        j3_update_list.append(
            UpdateOne(
                {"_id": i["_id"]},
                {"$set": {
                    "default_user": i.get("default_user"),
                    "teams": i.get("teams", {}),
                    "user_data": i.get("user_data", {}),
                    "partner": i.get("partner"),
                    "partner_request": i.get("partner_request", []),
                }},
                True
            )
        )
    if jianghu_update_list:
        client["jianghu"]["user"].bulk_write(jianghu_update_list)
    if j3_update_list:
        client["jx3_data"]["j3_user"].bulk_write(j3_update_list)
    client["my_bot"]["user_info"].update_many({}, {"$unset": {
        "river_lantern": 1,
        "gold": 1,
        "gua": 1,
        "is_sign": 1,
        "default_user": 1,
        "teams": 1,
        "user_data": 1,
        "user_lucky": 1,
        "energy": 1,
        "当前气海": 1,
        "contribution": 1,
        "discard_equipment_num": 1,
        "dungeon_num": 1,
        "last_sign": 1,
        "world_boss_num": 1,
        "partner": 1
    }})

    food_list = []
    for i in client["sources"]["food"].find():
        food_list.append(UpdateOne({"_id": i["_id"]}, {"$set": {"content": i["_id"]}}, True))
    if food_list:
        client["sources"]["food"].bulk_write(food_list)
    kfc_list = []
    del_kfc_list = []
    for i in client["sources"]["kfc"].find():
        md5_id = hashlib.md5(i["content"].encode("utf-8")).hexdigest()
        kfc_list.append(UpdateOne({"_id": md5_id}, {"$set": {"content": i["content"], "update_time": i["update_time"]}}, True))
        if md5_id != i["_id"]:
            del_kfc_list.append(DeleteOne({"_id": i["_id"]}))
    if kfc_list:
        client["sources"]["kfc"].bulk_write(kfc_list)
    if del_kfc_list:
        client["sources"]["kfc"].bulk_write(del_kfc_list)
    memes_list = []
    for i in client["sources"]["memes"].find():
        if i.get("url"):
            memes_list.append(UpdateOne({"_id": i["_id"]}, {"$set": {"content": i["url"]}, "$unset": {"url":1}}, True))
    if memes_list:
        client["sources"]["memes"].bulk_write(memes_list)

    client["my_bot"]["bot_conf"].update_one({"_id": 1}, {"$set": {"db_version": "1.0.0"}}, True)


version_update_func = {
    "0.0.0": v_0_0_0
}

if __name__ == "__main__":
    db_version = client["my_bot"]["bot_conf"].find_one({"_id": 1}).get("db_version", "0.0.0")
    lastest_version = "1.0.0"
    while db_version != lastest_version:
        version_update_func[db_version]()
        db_version = client["my_bot"]["bot_conf"].find_one({"_id": 1}).get("db_version", "0.0.0")
