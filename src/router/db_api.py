import math
import time
import random
from datetime import datetime, timedelta

from bson import ObjectId
from pymongo import UpdateOne
from passlib.context import CryptContext

from src.utils.db import jx3_data, my_bot, management, source



class DB():

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(DB, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    # Bot
    def get_bot_list(self, page=1, filter={}):
        try:
            data = []
            limit = 20
            skip = limit * (page - 1)
            count = management.bot_info.count_documents(filter)
            page_count = math.ceil(count / limit)
            sort = [("login_data", -1), ("online_status", -1), ("enable", -1)]
            result = management.bot_info.find(filter=filter,
                                              sort=sort,
                                              limit=limit,
                                              skip=skip)
            for i in result:
                group_num = management.group_conf.count_documents(
                    {"bot_id": i["_id"]})
                if i.get("login_data"):
                    login_data = i["login_data"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    login_data = "-"
                i.update({"group_num": group_num, "login_data": login_data})
                data.append(i)
            return data, page_count
        except Exception:
            return {}

    def set_bot(self, bot_id, set_data):
        try:
            management.bot_info.update_one({"_id": bot_id}, {"$set": set_data},
                                           True)
            return True
        except Exception:
            return False

    def del_bot(self, bot_id):
        try:
            management.bot_info.delete_one({"_id": bot_id})
            return True
        except Exception:
            return False

    # User

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def get_user_info(self, username):
        return management.user.find_one({"_id": username})

    def add_user(self, register_item):
        if management.user.find_one({"_id": register_item.username}):
            return {'code': 400, 'msg': "用户重复"}
        now_time = datetime.now()
        vcode = management.verification_code.find_one_and_delete({
            "_id":
            register_item.username,
            "verifycode":
            register_item.verifycode,
            "create_time": {
                "$gte": now_time + timedelta(minutes=-30)
            }
        })
        if not vcode:
            return {'code': 400, 'msg': "验证码错误或已过期"}
        management.user.insert_one({
            "_id":
            register_item.username,
            "password":
            self.get_password_hash(register_item.password),
            "login_time":
            now_time,
            "num_of_fail":
            0,
            "user_permission":
            1
        })
        return {'code': 200, 'msg': "注册成功"}

    def create_verification_code(self, username):
        if management.user.find_one({"_id": username}):
            return 400, "用户重复"
        vcode = "".join(random.choices("1234567890", k=6))
        management.verification_code.update_one({"_id": username}, {
            "$set": {
                "_id": username,
                "verifycode": vcode,
                "create_time": datetime.now()
            }
        }, True)
        return 200, vcode

    def verify_user(self, username, password):
        """
        检查用户与密码是否匹配
        每次检查都会更新用户表中的login_time
        每次检查失败, 用户表中num_of_fail会+1
        若num_of_fail>= 5, 检查失败后需要等待300
        """
        fucking_time = 300
        fucking_numb = 5
        usr = management.user.find_one({"_id": username})
        if usr:
            now_time = datetime.now()
            login_time = usr.get("login_time", now_time)
            sleep_time = fucking_time - (now_time - login_time).seconds
            num_of_fail = usr.get("num_of_fail", 0)
            if num_of_fail >= fucking_numb and sleep_time > 0:
                m, s = divmod(sleep_time, 60)
                return False, f"账户已被锁定, 请在{m}分{s}秒后重新尝试"
            usr_pwd = usr.get("password")
            if self.verify_password(password, usr_pwd):
                management.user.update_one(
                    {"_id": username},
                    {"$set": {
                        "num_of_fail": 0,
                        "login_time": now_time
                    }}, True)
                return True, usr["user_permission"]
            else:
                cur_num_of_fail = num_of_fail + 1 if num_of_fail < fucking_numb else num_of_fail
                management.user.update_one({"_id": username}, {
                    "$set": {
                        "num_of_fail": cur_num_of_fail,
                        "login_time": now_time
                    }
                }, True)
                if cur_num_of_fail >= fucking_numb:
                    return False, f"密码错误, 账号已被锁定, {fucking_time//60} 分钟后再来吧"
                return False, f"密码错误, 失败{fucking_numb-cur_num_of_fail}次后账号将被锁定 {fucking_time//60} 分钟"
        else:
            return False, "用户不存在"

    # BlackList
    def get_black_list(self):
        """获取所有的黑名单"""
        today = int(time.mktime(datetime.now().timetuple())) * 1000
        data = {
            "user_black_list":
            list(
                management.user_black_list.find({"block_time": {
                    "$gt": today
                }})),
            "group_black_list":
            list(
                management.group_black_list.find(
                    {"block_time": {
                        "$gt": today
                    }}))
        }
        return True, data

    def set_black_list(self, num_type, number, block_time, action, remark):
        """加黑"""
        if num_type == "QQ":
            black_list = management.user_black_list
        elif num_type == "群号":
            black_list = management.group_black_list
        else:
            return False, "请求的数据不对!"
        update = {"$set": {"block_time": block_time, "remark": remark}}
        if action == "add":
            update.update({"$inc": {"black_num": 1}})
        black_list.update_one(filter={"_id": int(number)},
                              update=update,
                              upsert=True)

        return True, "操作成功!"

    def get_river_lantern(self):
        """获取河灯"""
        sort = list({'last_sent': -1}.items())
        data = []
        for i in my_bot.river_lantern.find({}, sort=sort, limit=20):
            i["last_sent"] = i["last_sent"].strftime("%Y-%m-%d %H:%M:%S")
            i["qlogo"] = f"http://q1.qlogo.cn/g?b=qq&nk={i['user_id']}&s=1"
            data.append(i)
        return list(data)

    # meme
    def add_meme(self, meme_id, meme_url):
        if source.memes.find_one({"_id": meme_id}):
            source.memes.update_one({"_id": meme_id},
                                    {"$set": {
                                        "update_time": datetime.now()
                                    }})
            return 500, "表情重复"
        source.memes.insert_one({
            "_id": meme_id,
            "url": meme_url,
            "update_time": datetime.now()
        })
        return 200, "添加成功"

    def del_meme(self, meme_id):
        source.memes.delete_one({"_id": meme_id})
        return 200, "删除成功"

    def get_meme(self, page=1):
        limit = 50
        skip = limit * (page - 1)
        count = source.memes.count_documents({})
        sort = list({'update_time': -1}.items())
        page_count = math.ceil(count / limit)
        res_data = list(source.memes.find(limit=limit, skip=skip, sort=sort))
        return 200, res_data, page_count

    def get_random_meme(self, count=1):
        max_count = 10
        if count > max_count:
            return 500, f"最多一次取{max_count}张"
        meme_list = [
            meme["url"] for meme in source.memes.aggregate([{
                "$sample": {
                    "size": count
                }
            }])
        ]
        return 200, meme_list

    # 疯狂星期四
    def add_kfc(self, content):
        _kfc = source.kfc.find_one({"content": content})
        if _kfc:
            source.kfc.update_one({"_id": _kfc["_id"]},
                                  {"$set": {
                                      "update_time": datetime.now()
                                  }})
            return 500, "文案重复"
        source.kfc.insert_one({
            "content": content,
            "update_time": datetime.now()
        })
        return 200, "添加成功"

    def del_kfc(self, kfc_id):
        source.kfc.delete_one({"_id": ObjectId(kfc_id)})
        return 200, "删除成功"

    def get_kfc(self, page=1):
        limit = 50
        skip = limit * (page - 1)
        count = source.kfc.count_documents({})
        sort = list({'update_time': -1}.items())
        page_count = math.ceil(count / limit)
        res_data = list(source.kfc.find(limit=limit, skip=skip, sort=sort))
        res_data = [{
            "_id": str(i["_id"]),
            "content": i["content"]
        } for i in res_data]
        return 200, res_data, page_count

    def get_random_kfc(self, count=1):
        max_count = 10
        if count > max_count:
            return 500, f"最多一次取{max_count}张"
        kfc_list = [
            kfc["content"] for kfc in source.kfc.aggregate([{
                "$sample": {
                    "size": count
                }
            }])
        ]
        return 200, kfc_list

    # 吃什么
    def add_food(self, contents: str):
        update_list = []
        for content in contents.split():
            update_list.append(
                UpdateOne({"_id": content},
                          {"$set": {
                              "update_time": datetime.now()
                          }}, True))
        source.food.bulk_write(update_list)
        return 200, f"添加成功"

    def del_food(self, food_id):
        source.food.delete_one({"_id": food_id})
        return 200, "删除成功"

    def get_food(self, page=1):
        limit = 500
        skip = limit * (page - 1)
        count = source.food.count_documents({})
        sort = list({'update_time': -1}.items())
        page_count = math.ceil(count / limit)
        res_data = list(source.food.find(limit=limit, skip=skip, sort=sort))
        res_data = [{"_id": i["_id"]} for i in res_data]
        return 200, res_data, page_count

    def get_random_food(self, count=1):
        max_count = 10
        if count > max_count:
            return 500, f"最多一次取{max_count}个"
        food_list = [
            food["_id"] for food in source.food.aggregate([{
                "$sample": {
                    "size": count
                }
            }])
        ]
        return 200, food_list

    # Team
    def get_team(self, team_id):
        try:
            filter = {"_id": team_id} if team_id else {}
            datas = jx3_data.j3_teams.find(filter)
            if not datas:
                return 204, "没有找到团队"
            return 200, list(datas)
        except Exception:
            return 500, "遇到麻烦了"

    def set_team(self, team_data, username):
        try:
            user_id = team_data["user_id"]
            user_info = my_bot.user_info.find_one({"_id": user_id})
            user_email = user_info.get("email") or f"{user_id}@qq.com"
            if user_email != username:
                return 403, "团队不属于你"
            jx3_data.j3_teams.update_one({"_id": team_data["_id"]},
                                         {"$set": team_data})
            return 200, "修改成功"
        except Exception:
            return 500, "遇到麻烦了"


db_api = DB()
