import re
from datetime import datetime
import math

from src.utils.log import logger
from src.utils.db import jianghu
from src.utils.email import mail_client
from src.plugins.jianghu.equipment import 材料等级表, 装备类型表
from src.plugins.jianghu.user_info import UserInfo
from nonebot.adapters.onebot.v11 import MessageSegment
from src.utils.browser import browser
from src.plugins.jianghu.shop import shop
from src.plugins.jianghu.gold import 减少银两, 增加银两


async def 上架商品(寄售人id, 商品名称, 价格, 备注=""):
    if int(价格) < 1:
        return "价格不能少于1两银子"
    if int(价格) > 100000000:
        return "价格不能多于100,000,000两银子"
    if len(备注) > 30:
        return "备注不能多于30个字"
    # 判断有无
    数量 = 1
    if re.findall("^[赤橙黄绿青蓝紫彩][金木水火土](\*\d+){0,1}$", 商品名称):
        类型 = "材料"
        等级 = 材料等级表[商品名称[0]]
        if "*" in 商品名称:
            商品名称, 数量 = 商品名称.split("*")
    elif re.findall("^(武器|外装|饰品)\d+(\*\d+){0,1}$", 商品名称):
        类型 = "图纸"
        等级 = int(商品名称[2:])
        if "*" in 商品名称:
            商品名称, 数量 = 商品名称.split("*")
    elif re.findall("^.{2,4}[剑杖扇灯锤甲服衫袍铠链牌坠玦环]$", 商品名称):
        类型 = 装备类型表[商品名称[-1]]
    elif 商品名称.split("*")[0] in shop:
        类型 = "物品"
        等级 = 1
        if "*" in 商品名称:
            商品名称, 数量 = 商品名称.split("*")
    else:
        return "找不到物品名字"
    数量 = int(数量)
    if 数量 < 1:
        return "上架数量必须大大于1"
    # 删除背包
    if 类型 in ("材料", "图纸"):
        con = jianghu.knapsack.find_one({"_id": 寄售人id})
        if not con or con.get(类型, {}).get(商品名称, 0) < 数量:
            return f"{商品名称}数量不足{数量}"
        con[类型][商品名称] -= 数量
        if con[类型][商品名称] == 0:
            del con[类型][商品名称]
        jianghu.knapsack.update_one({"_id": 寄售人id}, {"$set": con}, True)
    elif 类型 in ("武器", "外装", "饰品"):
        con = jianghu.equip.find_one({"_id": 商品名称})
        if not con or 寄售人id != con.get("持有人", 0):
            return "你没有这件装备"
        交易时间 = con.get("交易时间")
        if 交易时间:
            交易保护时间 = 120 - (datetime.now() - 交易时间).seconds
            if 交易保护时间 > 0:
                return f"{商品名称}正在交易保护期间，无法售卖。剩余时间：{交易保护时间}秒"
        装备 = jianghu.user.find_one({"_id": 寄售人id})["装备"]
        if 商品名称 == 装备[con["类型"]]:
            return "该装备正在使用，无法上架"
        等级 = con.get("装备分数", 0)
        jianghu.equip.update_one({"_id": 商品名称}, {"$set": {"持有人": -1}}, True)
    elif 类型 == "物品":
        con = jianghu.knapsack.find_one({"_id": 寄售人id})
        if con.get(商品名称, 0) < 数量:
            return f"{商品名称}数量不足{数量}"
        jianghu.knapsack.update_one({"_id": 寄售人id}, {"$inc": {商品名称: -数量}})

    data = {
        "类型": 类型,
        "等级": 等级,
        "价格": int(价格),
        "名称": 商品名称,
        "寄售人": 寄售人id,
        "日期": datetime.now(),
        "数量": 数量,
        "关注": 0,
        "备注": 备注
    }
    # 上架
    编号 = jianghu.insert_auto_increment("auction_house", data)
    logger.info(f"上架商品: {寄售人id} 上架{商品名称}({编号})成功！")
    return f"上架[{商品名称}]成功！商品编号：{编号}"


async def 我的商品(操作人id, 命令):
    filter = {"寄售人": 操作人id}
    总数 = jianghu.auction_house.count_documents(filter)
    当前页 = 1
    if 当前页re := re.findall("\d+", 命令):
        当前页 = int(当前页re[0])
    limit = 15
    skip = (当前页 - 1) * limit
    页数 = math.ceil(总数 / limit)
    if 当前页 > 页数:
        return f"只能查到{页数}页"
    result = jianghu.auction_house.find(filter=filter, limit=limit, skip=skip)
    datas = []
    for i in result:
        寄售人 = UserInfo(i["寄售人"])
        datas.append({
            "编号": i["_id"],
            "类型": i["类型"],
            "等级": i["等级"],
            "价格": f"{i['价格']:,}",
            "名称": i["名称"],
            "寄售人": 寄售人.基础属性['名称'],
            "日期": i["日期"].strftime("%Y-%m-%d"),
            "关注": i["关注"],
            "数量": i.get("数量", 1),
            "备注": i["备注"],
        })
    pagename = "./江湖/交易行.html"
    img = await browser.template_to_image(pagename=pagename,
                                          datas=datas,
                                          当前页=当前页,
                                          页数=页数)
    return MessageSegment.image(img)


async def 下架商品(操作人id, 商品id):
    # 寄售人id是否等于操作人id
    商品 = jianghu.auction_house.find_one({"_id": 商品id})
    if not 商品:
        return "商品不存在！"
    商品类型 = 商品["类型"]
    商品名称 = 商品["名称"]
    商品数量 = 商品.get("数量", 1)
    寄售人 = 商品["寄售人"]
    if 寄售人 != 操作人id:
        return "这个商品不是你寄售的！"

    # 获得商品
    if 商品类型 in ("材料", "图纸"):
        con = jianghu.knapsack.find_one({"_id": 操作人id})
        if not con:
            con = {}
        if not con.get(商品类型):
            con[商品类型] = {}
        if not con[商品类型].get(商品名称):
            con[商品类型][商品名称] = 0
        con[商品类型][商品名称] += 商品数量
        jianghu.knapsack.update_one({"_id": 操作人id}, {"$set": con}, True)
    elif 商品类型 in ("武器", "外装", "饰品"):
        jianghu.equip.update_one({"_id": 商品名称}, {"$set": {"持有人": 操作人id}}, True)
    elif 商品类型 == "物品":
        jianghu.knapsack.update_one({"_id": 操作人id}, {"$inc": {商品名称: 商品数量}}, True)
    # 交易行删除商品
    jianghu.auction_house.delete_one({"_id": 商品id})
    logger.info(f"下架商品: {操作人id}下架{商品名称}({商品id})*{商品数量}成功！")
    return f"下架{商品名称}成功！"


async def 购买商品(购买人id, 名称):
    购买人 = UserInfo(购买人id)
    凶煞 = 购买人.基础属性["凶煞"]
    if 凶煞 > datetime.now():
        return f"凶煞状态无法购买物品，凶煞状态结束时间：{凶煞.strftime('%Y-%m-%d %H:%M:%S')}"
    数量 = 1
    商品id = 名称
    if "*" in 名称:
        商品id, 数量 = 名称.split("*")
    商品 = jianghu.auction_house.find_one({"_id": int(商品id)})
    if not 商品:
        return "商品不存在！"
    数量 = int(数量)
    商品id = 商品["_id"]
    商品价格 = 商品["价格"]
    商品类型 = 商品["类型"]
    商品名称 = 商品["名称"]
    寄售人 = 商品["寄售人"]
    商品数量 = 商品.get("数量", 1)
    if 商品数量 < 数量:
        return f"该商品只有{商品数量}件了"
    总价 = 商品价格 * 数量
    if not await 减少银两(购买人id, 总价, "交易行购买"):
        return f"\n购买商品[{商品id}]({商品名称})*{数量}失败，需要银两{商品价格}"
    # 获得商品
    if 商品类型 in ("材料", "图纸"):
        con = jianghu.knapsack.find_one({"_id": 购买人id})
        if not con:
            con = {}
        if not con.get(商品类型):
            con[商品类型] = {}
        if not con[商品类型].get(商品名称):
            con[商品类型][商品名称] = 0
        con[商品类型][商品名称] += 数量
        jianghu.knapsack.update_one({"_id": 购买人id}, {"$set": con}, True)
    elif 商品类型 in ("武器", "外装", "饰品"):
        jianghu.equip.update_one({"_id": 商品名称}, {"$set": {"持有人": 购买人id, "交易时间": datetime.now()}}, True)
    elif 商品类型 == "物品":
        jianghu.knapsack.update_one({"_id": 购买人id}, {"$inc": {商品名称: 数量}}, True)
    # 交易行删除商品
    if 商品数量 - 数量 <= 0:
        jianghu.auction_house.delete_one({"_id": 商品id})
    else:
        jianghu.auction_house.update_one({"_id": 商品id}, {"$inc": {"数量": -数量}})
    # 寄售人获得 银两 使用qq邮箱接收信息
    手续费 = 总价 // 100
    获得银两 = 总价 - 手续费
    await 增加银两(寄售人, 获得银两, "交易行出售")

    当前时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await mail_client.send_mail(
        寄售人, f"{商品名称}售卖成功通知",
        f"您寄售的[{商品名称}]于{当前时间}，被【{购买人.基础属性['名称']}】买走[{数量}]个\n共计价格{总价}两银子。扣除手续费{手续费}，共获得{获得银两}")
    logger.info(f"购买商品: {寄售人}[{商品名称}] -({商品价格}*{数量})-> {购买人.基础属性['名称']}({购买人id})")
    msg = f"购买商品完成\n花费{总价}两银子，获得[{商品名称}*{数量}]"
    return msg


async def 查找商品(condition=""):
    condition_list = condition.split()
    filter = {}
    sort = {}
    for i in condition_list[1:]:
        if re.findall(".+\d+-\d+", i):
            if i[:2] not in ("等级", "价格"):
                continue
            n1, n2 = [int(n) for n in i[2:].split("-")]
            if n1 > n2:
                n2, n1 = n1, n2
            filter[i[:2]] = {"$gte": n1, "$lte": n2}
        elif re.findall("^(等级|价格|日期|关注|数量)[-\+]{0,1}$", i):
            sort[i[:2]] = -1 if i[-1] == "-" else 1
        elif re.findall("^[（\(].+[\)）]$", i):
            filter["备注"] = {"$regex": i[1:-1]}
        elif i == condition_list[1]:
            if i in ("武器", "外装", "饰品", "图纸", "材料", "秘籍", "其他"):
                filter["类型"] = i
            else:
                filter["名称"] = {"$regex": i}
    if not sort:
        sort = {"日期": -1}
    总数 = jianghu.auction_house.count_documents(filter)
    当前页 = 1
    if 当前页re := re.findall("\d+", condition_list[0]):
        当前页 = int(当前页re[0])
    limit = 15
    skip = (当前页 - 1) * limit
    页数 = math.ceil(总数 / limit)
    if 当前页 > 页数:
        return f"只能查到{页数}页"
    result = jianghu.auction_house.find(filter=filter,
                                   sort=list(sort.items()),
                                   limit=limit,
                                   skip=skip)
    datas = []
    for i in result:
        寄售人 = UserInfo(i["寄售人"])
        datas.append({
            "编号": i["_id"],
            "类型": i["类型"],
            "等级": i["等级"],
            "价格": f"{i['价格']:,}",
            "名称": i["名称"],
            "寄售人": 寄售人.基础属性['名称'],
            "日期": i["日期"].strftime("%Y-%m-%d"),
            "数量": i.get("数量", 1),
            "关注": i["关注"],
            "备注": i["备注"],
        })
    pagename = "./江湖/交易行.html"
    img = await browser.template_to_image(pagename=pagename,
                                          datas=datas,
                                          当前页=当前页,
                                          页数=页数)
    return MessageSegment.image(img)

