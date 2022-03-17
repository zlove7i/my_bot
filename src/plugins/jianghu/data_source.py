import math
import random
import copy
import re
import os
from datetime import datetime

from nonebot.adapters.onebot.v11 import Bot
from src.plugins.jianghu.user_info import UserInfo
from src.plugins.jianghu.skill import Skill

from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from src.utils.db import db
from src.utils.log import logger
from src.utils.browser import browser
from src.plugins.jianghu.shop import shop
from src.plugins.jianghu.equipment import 打造装备, 合成图纸, 合成材料, 装备价格, 材料等级表
from src.plugins.jianghu.jianghu import PK
from src.plugins.jianghu.world_boss import world_boss, start_resurrection_world_boss
from src.utils.cooldown_time import search_record, search_once
from src.plugins.jianghu.dungeon import 挑战秘境, 查看秘境, 秘境进度


client = AsyncClient()
'''异步请求客户端'''


async def get_my_info(user_id: int, user_name: str) -> Message:
    '''
    :说明
        个人信息

    :参数
        * user_id：用户QQ

    :返回
        * Message：机器人返回消息
    '''

    _con = db.user_info.find_one({'_id': user_id})
    if not _con:
        _con = {}
    last_sign = _con.get("last_sign")
    today = datetime.today()
    suangua_data = {}
    if last_sign and today.date() == last_sign.date():
        suangua_data = _con.get("gua", {})
    gold = _con.get("gold", 0)
    jianghu_data = UserInfo(user_id)
    user_stat = jianghu_data.当前状态
    user_stat["当前气血"] = jianghu_data.当前气血
    user_stat["当前内力"] = jianghu_data.当前内力
    base_attribute = jianghu_data.基础属性
    pagename = "my_info.html"
    img = await browser.template_to_image(user_name=user_name,
                                          user_id=user_id,
                                          pagename=pagename,
                                          gold=gold,
                                          user_stat=user_stat,
                                          base_attribute=base_attribute,
                                          suangua_data=suangua_data)
    return MessageSegment.image(img)


async def set_name(user_id, res):
    if not res:
        return "输入错误"
    name = res[0]
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
    match = zhPattern.search(name)
    if not match:
        return "名字需要八字以内的汉字"
    if db.jianghu.find_one({"名称": name}) or name == "无名":
        return "名称重复"
    usr = UserInfo(user_id)
    if usr.名称 != "无名":
        msg = "，花费一百两银子。"
        gold = 0
        con = db.user_info.find_one({"_id": user_id})
        if con:
            gold = con.get("gold", 0)
        if gold < 100:
            return "改名需要花费一百两银子，你的银两不够！"
        db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -100}})
    else:
        msg = "，首次改名不需要花费银两。"
    db.jianghu.update_one({"_id": user_id}, {"$set": {"名称": name}}, True)
    return "改名成功" + msg


async def give_gold(user_id, user_name, at_qq, gold):
    '''赠送银两'''

    logger.debug(f"赠送银两 | <e>{user_id} -> {at_qq}</e> | {gold}")
    con = db.user_info.find_one({"_id": user_id})
    if not con:
        con = {}
    if con.get("gold", 0) < gold:
        logger.debug(f"赠送银两 | <e>{user_id} -> {at_qq}</e> | <r>银两不足</r>")
        return f"{user_name}，你的银两不足！"
    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -gold}}, True)
    db.user_info.update_one({"_id": at_qq}, {"$inc": {"gold": gold}}, True)
    logger.debug(f"赠送银两 | <e>{user_id} -> {at_qq}</e> | <g>成功！</g>")
    return f"成功赠送{gold}两银子！"


async def purchase_goods(user_id, res):
    if len(res) > 2:
        return "输入错误"
    数量 = 1
    商品 = res[0]
    价格 = shop.get(商品, {}).get("价格")
    if len(res) == 2:
        数量 = int(res[1])
    if not 价格:
        return "找不到物品"
    if 数量 < 1:
        return "数量不可以小于1"
    总价 = 价格 * 数量
    con = db.user_info.find_one({"_id": user_id})
    if not con:
        con = {}
    if con.get("gold", 0) < 总价:
        logger.debug(f"购买商品 | {商品} | <e>{user_id}</e> | <r>银两不足</r>")
        return f"你的银两不足！"
    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -总价}}, True)
    db.knapsack.update_one({"_id": user_id}, {"$inc": {商品: 数量}}, True)
    return "购买成功!"


async def use_goods(user_id, res):
    if len(res) > 2:
        return "输入错误"
    数量 = 1
    物品 = res[0]
    使用物品 = shop.get(物品, {}).get("使用")
    使用数量限制 = shop.get(物品, {}).get("使用数量", 1)
    if not 使用物品:
        return "物品不存在"
    if len(res) == 2:
        数量 = int(res[1])
    if 数量 > 使用数量限制:
        return f"该物品一次只能用{使用数量限制}个"
    con = db.knapsack.find_one({"_id": user_id})
    if not con:
        con = {}
    if con.get(物品, 0) < 数量:
        logger.debug(f"使用物品 | {物品} | <e>{user_id}</e> | <r>物品数量不足</r>")
        return f"你的物品数量不足！"
    user_info = UserInfo(user_id)
    db.knapsack.update_one({"_id": user_id}, {"$inc": {物品: -数量}}, True)
    msg = 使用物品(user_info, 数量)
    return msg


async def remove_equipment(user_id, 装备名称):
    """摧毁装备"""
    con = db.equip.find_one({"_id": 装备名称})
    if not con:
        return "该装备不存在"
    if con["持有人"] != user_id:
        return "你没有此装备"
    if con.get("标记"):
        return "该装备已被标记，无法摧毁"
    装备 = db.jianghu.find_one({"_id": user_id})["装备"]
    if 装备名称 == 装备[con["类型"]]:
        return "该装备正在使用，无法摧毁"

    db.equip.delete_one({"_id": 装备名称})
    return f"成功摧毁装备{装备名称}"


async def tag_gear(user_id, 装备名称: str, 标记: str):
    '''标记装备'''
    if 标记 and len(标记) != 2:
        return "标记必须为两个字"
    con = db.equip.find_one({"_id": 装备名称})
    if not con:
        return "该装备不存在"
    if con["持有人"] != user_id:
        return "你没有此装备"
    if 标记:
        db.equip.update_one({"_id": 装备名称}, {"$set": {"标记": 标记}}, True)
    else:
        db.equip.update_one({"_id": 装备名称}, {"$unset": {"标记": 1}}, True)
    return "标记成功！"


async def sell_equipment(user_id, 装备名称: str):
    '''出售装备'''
    获得银两 = 0
    if 装备名称.isdigit():
        售卖分数 = int(装备名称)
        cons = db.equip.find({"持有人": user_id})
        for con in cons:
            装备名称 = con['_id']
            装备 = db.jianghu.find_one({"_id": user_id})["装备"]
            if 装备名称 == 装备[con["类型"]] or con.get("标记"):
                continue
            银两 = 装备价格(con)
            if 银两 < 售卖分数:
                获得银两 += 银两
                db.equip.delete_one({"_id": 装备名称})
    else:
        con = db.equip.find_one({"_id": 装备名称})
        if not con:
            return "该装备不存在"
        if con["持有人"] != user_id:
            return "你没有此装备"
        装备 = db.jianghu.find_one({"_id": user_id})["装备"]
        if 装备名称 == 装备[con["类型"]]:
            return "该装备正在使用，无法出售"
        获得银两 += 装备价格(con)
        db.equip.delete_one({"_id": 装备名称})
    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": 获得银两}}, True)

    return f"出售成功，获得银两：{获得银两}"


async def rebuild_equipment(user_id, 装备一名称, 装备二名称):
    '''重铸装备'''
    if 装备一名称[-1] != 装备二名称[-1]:
        return "同类型装备才可以重铸"
    装备 = db.jianghu.find_one({"_id": user_id})["装备"]
    装备一 = db.equip.find_one({"_id": 装备一名称})
    if not 装备一:
        return "装备一不存在"
    if 装备一["持有人"] != user_id:
        return "你没有装备一"
    装备二 = db.equip.find_one({"_id": 装备二名称})
    if not 装备二:
        return "装备二不存在"
    if 装备二.get("标记"):
        return f"{装备二名称}已被标记，只能作为保留属性的装备（第一槽位）进行重铸。"
    if 装备二["持有人"] != user_id:
        return "你没有装备二"
    if 装备一名称 == 装备[装备一["类型"]]:
        return "该装备一正在使用，无法重铸"
    if 装备二名称 == 装备[装备二["类型"]]:
        return "该装备二正在使用，无法重铸"
    del 装备一["_id"]
    db.equip.update_one({"_id": 装备二名称}, {"$set": 装备一})
    db.equip.delete_one({"_id": 装备一名称})
    return "装备重铸成功"


async def build_equipment(user_id, res):
    if len(res.split()) != 3:
        return "输入错误"
    材料re = re.compile(" ([赤橙黄绿青蓝紫][金木水火土])")
    材料list = 材料re.findall(res)
    图纸re = re.compile(" ([武器外装饰品]{2}\d+)")
    图纸list = 图纸re.findall(res)
    if not all([材料list, 图纸list]):
        return "输入错误"
    材料名称 = 材料list[0]
    图纸名称 = 图纸list[0]

    con = db.knapsack.find_one({"_id": user_id})
    if con:
        材料 = con.get("材料", {})
        图纸 = con.get("图纸", {})
        材料数量 = 材料.get(材料名称, 0)
        图纸数量 = 图纸.get(图纸名称, 0)
    if 材料数量 < 1:
        return "材料不足"
    if 图纸数量 < 1:
        return "图纸不足"
    材料数量 -= 1
    材料[材料名称] = 材料数量
    if 材料数量 == 0:
        del 材料[材料名称]
    图纸数量 -= 1
    图纸[图纸名称] = 图纸数量
    if 图纸数量 == 0:
        del 图纸[图纸名称]
    db.knapsack.update_one({"_id": user_id}, {"$set": {
        "材料": 材料,
        "图纸": 图纸
    }}, True)
    装备 = 打造装备(材料名称, 图纸名称)
    装备["打造人"] = user_id
    装备["持有人"] = user_id
    装备["打造日期"] = datetime.now()
    db.equip.insert_one(装备)
    msg = f"打造成功！\n装备名称：{装备['_id']}（{装备['装备分数']}）\n基础属性：{装备['基础属性']}\n"
    if 装备.get("附加属性"):
        msg += f"附加属性：{装备['附加属性']}\n"
    打造人 = db.jianghu.find_one({'_id': 装备['打造人']})
    msg += f"打造人：{打造人['名称']}\n打造时间：{装备['打造日期'].strftime('%Y-%m-%d %H:%M:%S')}"
    return msg


async def compose(user_id, res):
    con = db.knapsack.find_one({"_id": user_id})
    if not con:
        return "物品不足"
    if res[0] == "合成材料":
        材料 = con.get("材料", {})
        材料限制等级 = 材料等级表["紫"]
        if len(res) == 2 and res[1].strip() in 材料等级表:
            材料限制等级 = 材料等级表[res[1].strip()]
        原始材料集合 = copy.deepcopy(材料)
        while True:
            材料副本 = copy.deepcopy(材料)
            for 材料名称, 材料数量 in 材料副本.items():
                材料等级 = 材料等级表[材料名称[0]]
                if 材料数量 < 3 or 材料等级 >= 材料限制等级:
                    continue
                合成结果, 获得材料 = 合成材料(材料名称)
                if 材料名称 == 获得材料:
                    材料[材料名称] -= 2
                else:
                    if 获得材料 not in 材料:
                        材料[获得材料] = 0
                    材料[获得材料] += 1
                    材料[材料名称] -= 3
                if 材料[材料名称] <= 0:
                    del 材料[材料名称]
            可继续合成数量 = [v for k, v in 材料.items() if v >= 3 and 材料等级表[k[0]] < 材料限制等级]
            if not 可继续合成数量:
                break
        db.knapsack.update_one({"_id": user_id}, {"$set": {"材料": 材料}}, True)

        最终合成结果 = {}
        for i in set(材料.keys()) & set(原始材料集合.keys()):
            if i not in 最终合成结果:
                最终合成结果[i] = 0
            最终合成结果[i] -= 原始材料集合.get(i, 0)
            最终合成结果[i] += 材料.get(i, 0)
        装备列表 = sorted(最终合成结果.items(), key=lambda x: x[1], reverse=True)
        return f"材料合成完成：{'、'.join([f'{k}{v:+}' for k, v in 装备列表 if v != 0])}"
    elif res[0] == "合成图纸":
        图纸 = con.get("图纸", {})
        if not 图纸:
            return "你没有图纸"
        用户图纸列表 = []
        过滤条件 = list(set(re.findall(r" *(武器|外装|饰品) *", " ".join(res))))
        用户输入图纸列表 = list(set(re.findall(r" *(武器\d+|外装\d+|饰品\d+) *", " ".join(res))))
        参与合成等级列表 = re.findall(r" (\d+) *", " ".join(res))
        参与合成等级 = 1500
        if 参与合成等级列表:
            参与合成等级 = int(参与合成等级列表[0])
            if 参与合成等级 > 1500:
                参与合成等级 = 1500
        用户图纸列表 = [i for i in 用户输入图纸列表 if i in 图纸]
        if 用户图纸列表:
            图纸列表 = 用户图纸列表
        else:
            图纸列表 = list(图纸.keys())
        图纸列表 = [i for i in 图纸列表 if int(i[2:]) <= 参与合成等级]
        if len(图纸列表) < 2:
            return "图纸不存在，或是输入的条件不太对。(单张图纸超过1500无法合成)"

        得到图纸列表 = []
        while True:
            if 用户图纸列表:
                图纸列表 = copy.deepcopy(用户图纸列表)
            else:
                图纸列表 = copy.deepcopy(图纸)
                图纸列表 = list(图纸列表.keys())
                if 过滤条件:
                    图纸列表 = [i for i in 图纸列表 if i[:2] in 过滤条件]
            图纸列表 = [i for i in 图纸列表 if int(i[2:]) <= 参与合成等级]
            图纸列表长度 = len(图纸列表)
            if 图纸列表长度 <= 1:
                break
            for i in range(1, 图纸列表长度, 2):
                消耗图纸列表 = (图纸列表[i-1], 图纸列表[i])
                获得图纸 = 合成图纸(*消耗图纸列表)
                if int(获得图纸[2:]) > 参与合成等级:
                    得到图纸列表.append(获得图纸)
                if not 图纸.get(获得图纸):
                    图纸[获得图纸] = 0
                图纸[获得图纸] += 1
                for 图纸耗材 in 消耗图纸列表:
                    图纸[图纸耗材] -= 1
                    if 图纸[图纸耗材] <= 0:
                        del 图纸[图纸耗材]
                if 用户图纸列表:
                    del 用户图纸列表[0]
                    del 用户图纸列表[0]
                    用户图纸列表.append(获得图纸)
        db.knapsack.update_one({"_id": user_id}, {"$set": {"图纸": 图纸}}, True)
        return "图纸合成完成：" + f"{'、'.join(得到图纸列表+图纸列表)}"
    return "输入错误"


async def ranking(user_id):
    con = db.knapsack.find_one({"_id": user_id}, projection={"_id": 0})
    if not con:
        return "你的背包啥都没有"
    user_info = UserInfo(user_id)
    data = {'物品': [], '名称': user_info.基础属性['名称']}
    for i in con:
        if not con[i]:
            continue
        if i == "材料":
            材料列表 = sorted(con[i].items(),
                          key=lambda x: 材料等级表[x[0][0]],
                          reverse=True)
            data['材料'] = 材料列表
        elif i == "图纸":
            图纸列表 = sorted(con[i].items(),
                          key=lambda x: int(x[0][2:]),
                          reverse=True)
            data['图纸'] = 图纸列表
        else:
            data['物品'].append({"名称": i, "数量": con[i]})
    pagename = "knapsack.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def my_gear(user_id, 内容):
    '''我的装备'''
    n = 1
    if isinstance(内容, str):
        limit = 20
        filter = {"持有人": user_id, "标记": 内容}
    else:
        limit = 10
        n = 内容
        filter = {"持有人": user_id}
    装备数量 = db.equip.count_documents(filter)
    页数 = math.ceil(装备数量 / limit)
    if n > 页数:
        return f"你只有{页数}页装备"
    cons = db.equip.find(filter)
    if not cons:
        return "你没有装备"
    msg = f"【装备 {n}/{页数}】"
    user_info = UserInfo(user_id)
    装备列表 = sorted(cons, key=lambda x: 装备价格(x), reverse=True)
    装备data_list = []
    for con in 装备列表[(n - 1) * 10:n * 10]:
        价格 = 装备价格(con)
        是否装备 = user_info.基础属性["装备"].get(con["类型"]) == con['_id']
        装备data = {"名称": con['_id'], "价格": 价格, "是否装备": 是否装备}
        if con.get('标记'):
            装备data['标记'] = f"[{con.get('标记')}]"
        装备data_list.append(装备data)
        msg += f"\n  {是否装备}{con['_id']} {价格}"
    user_info.基础属性['名称']
    data = {"持有人": user_info.基础属性['名称'], "页数": 页数, "当前页": n, "装备": 装备data_list}
    pagename = "equip.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def check_gear(bot, res):
    """查看装备"""
    if not res:
        return "查看格式错误"
    gear_name = res[0]
    if gear_name.isdigit():
        if con := db.auction_house.find_one({"_id": int(gear_name)}):
            gear_name = con.get("名称", "")
    data = db.equip.find_one({"_id": gear_name})
    if not data:
        return "查不到此装备"
    打造人_info = UserInfo(data['打造人'])
    data['打造人'] = 打造人_info.基础属性['名称']
    if data['持有人'] == -1:
        data['持有人'] = "售卖中"
    else:
        持有人_info = UserInfo(data['持有人'])
        data['持有人'] = 持有人_info.基础属性['名称']
    data['打造日期'] = data['打造日期'].strftime("%Y-%m-%d")
    pagename = "check_equip.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def use_gear(user_id, res):
    """使用装备"""
    if not res:
        return "输入格式错误"
    gear_name = res[0]
    if len(gear_name) == 2:
        cons = db.equip.find({"持有人": user_id, "标记": gear_name})
        if not cons:
            return "找不到被标记的装备"
    else:
        con = db.equip.find_one({"_id": gear_name})
        if not con:
            return "不存在这件装备"
        if con["持有人"] != user_id:
            return "你没有这件装备"
        cons = [con]
    user_info = UserInfo(user_id)
    for con in cons:
        装备 = user_info.基础属性["装备"]
        装备.update({con['类型']: con['_id']})
    db.jianghu.update_one({'_id': user_id}, {"$set": {"装备": 装备}})
    return f"装备{gear_name}成功"


async def pk_world_boss(user_id, res):
    """世界首领"""
    世界首领名称 = ""
    if res:
        世界首领名称 = res[0]
    data = await world_boss(user_id, 世界首领名称)
    if isinstance(data, str):
        return data
    pagename = "pk.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def start_dungeon(user_id, res):
    """挑战秘境"""
    秘境首领 = ""
    if res:
        秘境首领 = res[0]
    data = await 挑战秘境(user_id, 秘境首领)
    if isinstance(data, str):
        return data
    pagename = "pk.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def view_dungeon(user_id, res):
    """查看秘境"""
    秘境名称 = ""
    if res:
        秘境名称 = res[0]
    return await 查看秘境(user_id, 秘境名称)


async def dungeon_progress(user_id):
    """秘境进度"""
    return await 秘境进度(user_id)


async def resurrection_world_boss():
    """复活世界首领"""
    start_resurrection_world_boss()


async def set_skill(user_id, res):
    """配置武学"""
    if len(res) != 2:
        return "输入格式错误"
    skill_name = res[0]
    skill_index = int(res[1]) - 1
    if skill_index > 4:
        return "技能槽位不能大于5"
    con = db.jianghu.find_one({"_id": user_id})
    已领悟武学 = []
    武学 = [""] * 5
    if con:
        已领悟武学 = con.get("已领悟武学", [])
        武学 = con.get("武学", 武学)
    if skill_name == "-":
        skill_name = ""
    elif skill_name not in 已领悟武学:
        return "你没有学会该武学"
    武学[skill_index] = skill_name
    db.jianghu.update_one({"_id": user_id}, {"$set": {"武学": 武学}}, True)
    return f"配置武学{skill_name}成功！"


async def comprehension_skill(user_id, res):
    """领悟武学"""
    if not res:
        return "输入格式错误"
    银两 = int(res[0])
    if 银两 <= 0:
        return "想领悟武学，多多少少的也得花一点银子吧……"
    拥有银两 = 0
    con = db.user_info.find_one({"_id": user_id})
    if con:
        拥有银两 = con.get("gold", 0)
    if 拥有银两 < 银两:
        return "你的银两不足"

    user_info = UserInfo(user_id)
    已领悟武学 = user_info.基础属性.get("已领悟武学", [])
    sl = Skill()
    全部武学 = list(sl.skill.keys())
    全部武学数量 = len(全部武学)
    已领悟武学数量 = len(已领悟武学)
    if 已领悟武学数量 == 全部武学数量:
        return "你已经学会了所有武学，不需要再领悟了！"

    # 检查领悟武学cd
    n_cd_time = 300
    app_name = "领悟武学"
    flag, cd_time = await search_record(user_id, app_name, n_cd_time)
    if not flag:
        msg = f"{cd_time} 后才可以继续领悟"
        return msg
    await search_once(user_id, app_name)

    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -银两}}, True)
    if random.randint(1, 100) < 银两:
        武学 = random.choice(全部武学)
        if 武学 in 已领悟武学:
            return "领悟失败"
    else:
        return "领悟失败"
    已领悟武学.append(武学)
    db.jianghu.update_one({"_id": user_id}, {"$set": {"已领悟武学": 已领悟武学}}, True)
    return f"花费{银两}两银子，成功领悟武学：{武学}"


async def impart_skill(user_id, at_qq, 武学):
    """传授武学"""
    user_info = UserInfo(user_id)
    if 武学 not in user_info.基础属性.get("已领悟武学", []):
        return "你都没学会这门招式，怎么传授给别人？"
    at_info = UserInfo(at_qq)
    被传授方武学 = at_info.基础属性.get("已领悟武学", [])
    if 武学 in 被传授方武学:
        return "对方已经学会了该武学，不用花冤枉钱了。"
    拥有银两 = 0
    con = db.user_info.find_one({"_id": user_id})
    if con:
        拥有银两 = con.get("gold", 0)
    需要花费银两 = 1000
    if 拥有银两 < 需要花费银两:
        return f"传授武学需要{需要花费银两}两银子，你的银两不足"
    被传授方武学.append(武学)
    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -需要花费银两}}, True)
    db.jianghu.update_one({"_id": at_qq}, {"$set": {"已领悟武学": 被传授方武学}}, True)
    return f"花费{需要花费银两}两银子，成功传授武学：{武学}"


async def pk_log(战斗编号):
    sk = Skill()
    战斗记录文件 = os.path.join(sk.战斗记录目录, 战斗编号)
    if not os.path.isfile(战斗记录文件):
        return "战斗记录不存在，只能查看当天的战斗记录"
    战斗记录 = []
    with open(战斗记录文件, "r", encoding="utf-8") as f:
        line = f.readline()
        while line:
            战斗记录.append(line)
            line = f.readline()
    data = {
        "战斗记录": 战斗记录
    }
    pagename = "pk_log.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def pk(动作, user_id, at_qq):
    战斗 = PK()
    data = 战斗.main(动作, user_id, at_qq)
    if isinstance(data, str):
        return data
    pagename = "pk.html"
    img = await browser.template_to_image(pagename=pagename, **data)
    return MessageSegment.image(img)


async def give(user_id, at_qq, 物品):
    材料re = re.compile(r"([赤橙黄绿青蓝紫][金木水火土])")
    图纸re = re.compile(r"([武器外装饰品]{2}\d+)")
    装备_re = re.compile(r"(.{2,4}[剑杖扇灯锤甲服衫袍铠链牌坠玦环])")
    if 材料re.match(物品):
        类型 = "材料"
    elif 图纸re.match(物品):
        类型 = "图纸"
    elif 装备_re.match(物品):
        类型 = "装备"
    elif 物品 in shop:
        类型 = "物品"
    else:
        return "你别逗我好不好?"
    if 类型 in ["材料", "图纸", "物品"]:
        con = db.knapsack.find_one({"_id": user_id})
        if not con:
            return "你的物品数量不足，请检查背包。"
        if 类型 == "物品":
            if con.get(物品, 0) < 1:
                return "你的物品数量不足，请检查背包。"
            db.knapsack.update_one({"_id": user_id}, {"$inc": {物品: -1}}, True)
            db.knapsack.update_one({"_id": at_qq}, {"$inc": {物品: 1}}, True)
        else:
            data = con.get(类型, {})
            if data.get(物品, 0) < 1:
                return "你的物品数量不足，请检查背包。"
            data[物品] -= 1
            if data[物品] <= 0:
                del data[物品]
            at_con = db.knapsack.find_one({"_id": at_qq})
            at_data = {物品: 0}
            if at_con:
                at_data = at_con.get(类型, {物品: 0})
            if not at_data.get(物品):
                at_data[物品] = 0
            at_data[物品] += 1
            db.knapsack.update_one({"_id": user_id}, {"$set": {
                类型: data
            }}, True)
            db.knapsack.update_one({"_id": at_qq}, {"$set": {
                类型: at_data
            }}, True)
    else:
        con = db.equip.find_one({"_id": 物品})
        if not con:
            return "不存在这件装备"
        if con["持有人"] != user_id:
            return "你没有这件装备"
        装备 = db.jianghu.find_one({"_id": user_id})["装备"]
        if 物品 == 装备[con["类型"]]:
            return "该装备正在使用，无法赠送"
            装备[con["类型"]] = ""
            db.jianghu.update_one({"_id": user_id}, {"$set": {"装备": 装备}})
        db.equip.update_one({"_id": 物品}, {"$set": {"持有人": at_qq}}, True)
    return "赠送成功"


async def healing(user_id, target_id):
    user = UserInfo(target_id)
    if not user.基础属性["重伤状态"]:
        return "未重伤，不需要疗伤"
    gold = 0
    con = db.user_info.find_one({"_id": user_id})
    if con:
        gold = con.get("gold", 0)
    if gold < 100:
        return "疗伤需要一百两银子，你的银两不够！"
    db.user_info.update_one({"_id": user_id}, {"$inc": {"gold": -100}}, True)
    db.jianghu.update_one({"_id": target_id}, {
        "$set": {
            "重伤状态": False,
            "当前气血": user.当前状态["气血上限"],
            "当前内力": user.当前状态["内力上限"]
        }
    }, True)
    return "花费一百两银子，疗伤成功！"


async def gold_ranking(bot: Bot, user_id):
    '''银两排行'''

    logger.debug(f"银两排行 | <e>{user_id}</e>")
    filter = {}
    sort = list({'gold': -1}.items())
    limit = 10
    msg = "银两排行\n"

    result = db.user_info.find(filter=filter, sort=sort, limit=limit)
    for n, i in enumerate(result):
        user_info = UserInfo(i['_id'])
        名称 = user_info.基础属性["名称"]
        if 名称 == "无名":
            ret = await bot.get_stranger_info(user_id=i['_id'], no_cache=False)
            名称 = ret['nickname']
        msg += f"{n+1} {名称} {i['gold']}\n"

    ret = db.user_info.aggregate([{
        "$sort": {
            "gold": -1
        }
    }, {
        "$group": {
            "_id": None,
            "all": {
                "$push": "$_id"
            }
        }
    }, {
        "$project": {
            "_id": 0,
            "index": {
                "$indexOfArray": ["$all", user_id]
            }
        }
    }])
    if not ret:
        msg += "\n找不到你的记录!"
        return msg
    index = list(ret)[0]["index"] + 1
    msg += f"\n你的排名:{index}"
    return msg

