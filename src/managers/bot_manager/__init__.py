import asyncio
import random
from datetime import datetime, timedelta

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import PrivateMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.plugin import on_regex
from pymongo import UpdateOne
from src.plugins.jianghu.auction_house import 下架商品
from src.plugins.jianghu.user_info import UserInfo
from src.utils.config import config
from src.utils.db import jianghu, jx3_data, logs, management, my_bot
from src.utils.log import logger
from src.utils.scheduler import scheduler

activation = on_regex(pattern=r"^激活$", priority=5, block=True)

set_instructions = on_regex(pattern=r"^修改使用说明 .+$", priority=5, block=True)

instructions = on_regex(pattern=r"^使用说明$",
                        permission=GROUP,
                        priority=3,
                        block=True)


@activation.handle()
async def _(bot: Bot, event: PrivateMessageEvent):
    bot_id = int(bot.self_id)
    bot_info = management.bot_info.find_one({"_id": bot_id})
    if bot_info.get("master"):
        return
    user_id = int(event.user_id)
    management.bot_info.update_one(
        {"_id": bot_id},
        {"$set": {
            "master": user_id,
            "enable": True,
            "access_group_num": 20
        }}, True)
    msg = "激活成功!"
    await activation.finish(msg)


@instructions.handle()
async def _(bot: Bot):
    '''使用说明'''
    msg = "https://docs.qq.com/doc/DVkNsaGVzVURMZ0ls"
    bot_id = int(bot.self_id)
    bot_info = management.bot_info.find_one({"_id": bot_id})
    if bot_info:
        msg = bot_info.get("instructions", msg)
    await instructions.finish(msg)


@set_instructions.handle()
async def _(bot: Bot, event: PrivateMessageEvent):
    '''修改使用说明'''
    user_id = event.user_id
    bot_id = int(bot.self_id)
    text = event.get_plaintext().split(" ", 1)[-1]
    bot_info = management.bot_info.find_one({"_id": bot_id})
    if bot_info.get("master") != user_id:
        return
    management.bot_info.update_one({"_id": bot_id},
                                   {"$set": {
                                       "instructions": text
                                   }}, True)
    await set_instructions.finish("修改成功")


async def archive_river_lantern():
    """河灯归档"""
    logger.info("河灯归档")
    river_lantern_info = my_bot.river_lantern.find(
        {'last_sent': {
            "$lte": datetime.today() + timedelta(days=-5)
        }})
    archive = my_bot.client["archive"]["river_lantern"]
    for lantern in river_lantern_info:
        my_bot.river_lantern.delete_one(lantern)
        del lantern["_id"]
        archive.insert_one(lantern)
    logger.info("河灯归档完成")


async def pull_off_shelves():
    """下架商品"""
    logger.info("下架商品")
    try:
        shelves = jianghu.auction_house.find(
            {'日期': {
                "$lte": datetime.today() + timedelta(days=-5)
            }})

        for i in shelves:
            await 下架商品(i["寄售人"], i["_id"])
        logger.info("自动下架商品完成")
    except Exception as e:
        logger.error(f"下架商品失败: {str(e)}")


async def reset_sign_nums():
    '''重置签到人数与福缘'''
    logger.info("正在重置签到人数")
    sign_num = my_bot.bot_conf.find_one({'_id': 1}).get("sign_num", 0)
    prize_pool = sign_num * 50000
    my_bot.bot_conf.update_one(
        {"_id": 1}, {'$set': {
            "sign_num": 0,
            "prize_pool": prize_pool
        }}, True)
    management.group_conf.update_many(
        {}, {'$set': {
            "add_group_num": 0
        }}, True)
    jianghu.user.update_many(
        {},
        {'$set': {
            "是否签到": False,
            "秘境次数": 0,
            "贡献": 0,
            "精力": 100,
            "丢弃装备次数": 0
        }}, True)
    logger.info("签到人数已重置")


async def 复活玩家():
    logger.info("正在复活玩家")
    project = {"_id": 1}
    users = []
    for i in jianghu.user.find({"重伤状态": True}, projection=project):
        user = UserInfo(i["_id"])
        users.append(
            UpdateOne({"_id": i["_id"]}, {
                "$set": {
                    "重伤状态": False,
                    "当前气血": user.当前状态["气血上限"],
                    "当前内力": user.当前状态["内力上限"]
                }
            }, True))
    jianghu.user.bulk_write(users)
    logger.info("玩家已复活")


def del_user_team(user_id, user_name, team_id):
    """删除用户信息表中的对应的团队"""
    j3_user = jx3_data.j3_user.find_one({"_id": user_id})
    user_teams = j3_user["teams"]
    if team_id in user_teams[user_name]:
        user_teams[user_name].remove(team_id)
        jx3_data.j3_user.update_one({"_id": user_id},
                                    {"$set": {
                                        "teams": user_teams
                                    }})


async def disband_team():
    meeting_time = datetime.now() - timedelta(minutes=60)
    team_infos = jx3_data.j3_teams.find(
        {"meeting_time": {
            "$lte": meeting_time
        }})
    for team_info in team_infos:
        team_id = team_info["_id"]
        logger.info(f"解散团队{team_id}")
        for members in team_info["team_members"]:
            for member in members:
                if member:
                    del_user_team(member["user_id"], member["user_name"],
                                  team_id)
        jx3_data.j3_teams.delete_one({"_id": team_id})


async def team_notice():
    meeting_time = datetime.now() + timedelta(minutes=30)
    team_infos = jx3_data.j3_teams.find({
        "meeting_time": {
            "$lte": meeting_time
        },
        "need_notice": True
    })
    if not team_infos:
        return
    notice_data = {}
    for team_info in team_infos:
        team_id = team_info["_id"]
        notice_data[team_id] = {
            "team_leader_name": team_info["team_leader_name"],
            "team_leader_id": team_info["user_id"],
            "team": {}
        }
        logger.info(f"开团通知{team_id}")
        for members in team_info["team_members"]:
            for member in members:
                if member:
                    user_id = member["user_id"]
                    group_id = member["group_id"]
                    bot_id = member["bot_id"]
                    if group_id not in notice_data[team_id]["team"]:
                        notice_data[team_id]["team"][group_id] = {
                            "bot_id": bot_id
                        }
                        notice_data[team_id]["team"][group_id]["user"] = []
                    notice_data[team_id]["team"][group_id]["user"].append(
                        user_id)

    for team_id, team_data in notice_data.items():
        for group_id, user_data in team_data["team"].items():
            try:
                bot = get_bot(str(user_data["bot_id"]))
            except KeyError as e:
                logger.warning(e)
            else:
                msg = f"团队【{team_id}】将于 30 分钟后集合，请提前做好准备。\n"\
                      f"团长：{team_data['team_leader_name']}({team_data['team_leader_id']})\n"\
                      f"可以发送“查看团队 {team_id}”查看团队信息\n"
                for user_id in set(user_data["user"]):
                    msg += MessageSegment.at(user_id)
                try:
                    await bot.send_group_msg(group_id=group_id, message=msg)
                    await asyncio.sleep(random.uniform(1, 5))
                except Exception:
                    logger.warning("开团通知发送失败")
        jx3_data.j3_teams.update_one({"_id": team_id},
                                     {"$set": {
                                         "need_notice": False
                                     }})


async def recovery_qihai():
    datas = jianghu.user.find({"$expr": {"$lt": ["$当前气海", "$气海上限"]}})
    for data in datas:
        data["当前气海"] += data["气海上限"] // 10
        if data["当前气海"] > data["气海上限"]:
            data["当前气海"] = data["气海上限"]
        jianghu.user.update_one({"_id": data["_id"]},
                                {"$set": {
                                    "当前气海": data["当前气海"]
                                }})


async def start_resurrection_world_boss():
    logger.info("正在复活世界首领")
    project = {"_id": 1, "体质": 1, "根骨": 1}
    if 已重伤首领 := jianghu.npc.find({
            "类型": "首领",
            "重伤状态": True
    },
                                 projection=project):
        已重伤首领列表 = list(已重伤首领)
        if 已重伤首领列表:
            复活首领 = random.choice(已重伤首领列表)
            jianghu.npc.update_one({"_id": 复活首领["_id"]}, {
                "$set": {
                    "重伤状态": False,
                    "当前气血": 复活首领["体质"] * 30,
                    "当前内力": 复活首领["根骨"] * 5
                }
            }, True)
    logger.info("世界首领已复活")


@scheduler.scheduled_job("cron", hour=4, minute=0)
async def _():
    '''每天4点开始偷偷的干活'''

    if config.is_main_host:
        await archive_river_lantern()
        await pull_off_shelves()


@scheduler.scheduled_job("cron", hour=0, minute=0)
async def _():
    '''0点重置'''
    # 重置战斗记录编号
    logs.counters.update_one({"_id": "pk_log"},
                             {"$set": {
                                 "sequence_value": 0
                             }})


@scheduler.scheduled_job("cron", minute="*")
async def _():
    """每分钟检测"""
    await disband_team()
    await team_notice()


@scheduler.scheduled_job("cron", hour="10,15,20,23", minute=1)
async def _():
    '''10,15,20, 23刷新世界boss'''
    if config.is_main_host:
        await start_resurrection_world_boss()


@scheduler.scheduled_job("cron", hour="8,21", minute=0)
async def _():
    '''8,20 复活玩家'''
    if config.is_main_host:
        await 复活玩家()

@scheduler.scheduled_job("cron", hour=7, minute=59)
async def _():
    '''每天八点重置签到人数'''
    if config.is_main_host:
        await reset_sign_nums()


@scheduler.scheduled_job("cron", hour="*")
async def _():
    if config.is_main_host:
        await recovery_qihai()
