from pymongo import MongoClient, UpdateOne
from src.utils.config import config

mg_list = config.mongodb.get("mongdb_list")
mg_usr = config.mongodb.get("mongodb_username")
mg_pwd = config.mongodb.get("mongodb_password")


client = MongoClient(f'mongodb://{",".join(mg_list)}/', username=mg_usr, password=mg_pwd)


def v_0_0_0_to_v_1_0_0():
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
                    "teams": i.get("teams", []),
                    "user_data": i.get("user_data", []),
                    "partner": i.get("partner"),
                    "partner_request": i.get("partner_request", []),
                }},
                True
            )
        )
    client["jianghu"]["user"].bulk_write(jianghu_update_list)
    client["jx3_data"]["j3_user"].bulk_write(j3_update_list)


if __name__ == "__main__":
    v_0_0_0_to_v_1_0_0()
