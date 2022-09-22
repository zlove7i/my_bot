from pymongo import MongoClient
from src.utils.config import config

mg_list = config.mongodb.get("mongdb_list")
mg_usr = config.mongodb.get("mongodb_username")
mg_pwd = config.mongodb.get("mongodb_password")

client = MongoClient(f'mongodb://{",".join(mg_list)}/',
                     username=mg_usr,
                     password=mg_pwd)


class DB(object):

    def __init__(self, db_name):
        """
        创建mongodb客户端
        """
        self.db = client[db_name]
        # 计数器
        self.counters = client["my_bot"].counters

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def insert_auto_increment(self, collection, data, id_name="_id"):
        _id = self.counters.find_one_and_update(
            filter={"_id": collection},
            update={"$inc": {"sequence_value": 1}},
            upsert=True
        )["sequence_value"]
        data.update(
            {id_name: _id}
        )
        self.db[collection].insert_one(data)
        return _id


class Management(DB):
    def __init__(self):
        super().__init__("management")
        self.group_black_list = self.db.group_black_list
        self.user_black_list = self.db.user_black_list
        self.bot_info = self.db.bot_info
        self.group_conf = self.db.group_conf
        self.user = self.db.user
        self.verification_code = self.db.verification_code


class Logs(DB):
    def __init__(self):
        super().__init__("logs")
        self.pk_log = self.db.pk_log

    def write_pk_log(self, log_data):
        return self.insert_auto_increment("pk_log", log_data, id_name="编号")

    def write_log(self, collection, log_data):
        self.db[collection].insert_one(log_data)


class Jx3Data(DB):
    def __init__(self):
        super().__init__("jx3_data")
        # 剑三团队
        self.j3_teams = self.db.j3_teams
        # tickets
        self.tickets = self.db.tickets
        # user_info
        self.j3_user = self.db.j3_user


class JiangHu(DB):
    def __init__(self):
        super().__init__("jianghu")
        self.knapsack = self.db.knapsack
        self.user = self.db.user
        self.equip = self.db.equip
        self.auction_house = self.db.auction_house
        self.npc = self.db.npc


class Sources(DB):
    def __init__(self):
        super().__init__("sources")
        # 表情包
        self.memes = self.db.memes
        self.kfc = self.db.kfc
        self.food = self.db.food


class MyBot(DB):
    def __init__(self):
        super().__init__("my_bot")
        # 机器人配置
        self.bot_conf = self.db.bot_conf
        # 群冷却时间配置
        self.group_cd_conf = self.db.group_cd_conf
        # 插件信息
        self.plugins_info = self.db.plugins_info
        # 用户信息
        self.user_info = self.db.user_info
        # 冷却时间记录
        self.search_record = self.db.search_record
        # 河灯
        self.river_lantern = self.db.river_lantern
        # 违禁词
        self.forbidden_word = self.db.forbidden_word


logs = Logs()
jianghu = JiangHu()
jx3_data = Jx3Data()
my_bot = MyBot()
management = Management()
sources = Sources()



if __name__ == "__main__":
    pass
