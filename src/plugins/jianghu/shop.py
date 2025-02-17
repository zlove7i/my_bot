import random
from src.utils.db import jianghu
from src.plugins.jianghu.user_info import UserInfo
from src.plugins.jianghu.gold import 增加银两


async def 材料盒(自己: UserInfo, 数量: int):
    user_id = 自己.基础属性["_id"]
    已有数量 = 0
    con = jianghu.knapsack.find_one({"_id": user_id})
    材料 = {}
    if con:
        材料 = con.get("材料", {})
    msg = "获得材料：\n"
    获取物品列表 = {}
    for _ in range(数量):
        材料属性 = random.choice("金木水火土")
        材料等级 = random.choice("赤橙")
        材料名称 = 材料等级 + 材料属性
        材料数量 = random.randint(1, 3)
        已有数量 = 材料.get(材料名称, 0)
        已有数量 += 材料数量
        材料.update({材料名称: 已有数量})
        if not 获取物品列表.get(材料名称):
            获取物品列表[材料名称] = 0
        获取物品列表[材料名称] += 材料数量
    msg += "、".join([f"{k} * {v}" for k, v in 获取物品列表.items()])
    jianghu.knapsack.update_one({"_id": user_id}, {"$set": {"材料": 材料}}, True)
    return True, msg


async def 图纸盒(自己: UserInfo, 数量: int):
    user_id = 自己.基础属性["_id"]
    con = jianghu.knapsack.find_one({"_id": user_id})
    图纸 = {}
    if con:
        图纸 = con.get("图纸", {})
    msg = "获得图纸：\n"
    获取物品列表 = {}
    for _ in range(数量):
        图纸样式 = random.choice(["武器", "外装", "饰品"])
        图纸等级 = random.randint(1, 3)
        图纸名称 = 图纸样式 + str(图纸等级)
        已有数量 = 0
        已有数量 = 图纸.get(图纸名称, 0)
        已有数量 += 1
        图纸.update({图纸名称: 已有数量})
        if not 获取物品列表.get(图纸名称):
            获取物品列表[图纸名称] = 0
        获取物品列表[图纸名称] += 1
    msg += "、".join([f"{k} * {v}" for k, v in 获取物品列表.items()])
    jianghu.knapsack.update_one({"_id": user_id}, {"$set": {"图纸": 图纸}}, True)
    return True, msg


async def 活血丹(自己: UserInfo, 数量: int):
    if 自己.基础属性["重伤状态"]:
        return "重伤状态下无法使用"
    for _ in range(数量):
        自己.当前气血 += 1000
    if 自己.当前气血 > 自己.当前状态["气血上限"]:
        自己.当前气血 = 自己.当前状态["气血上限"]
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                          {"$set": {
                              "当前气血": 自己.当前气血,
                          }}, True)
    return True, f"使用活血丹成功，当前气血为{自己.当前气血}"


async def 大活血丹(自己: UserInfo, 数量: int):
    if 自己.基础属性["重伤状态"]:
        return "重伤状态下无法使用"

    自己.当前气血 = 自己.当前状态["气血上限"]
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                          {"$set": {
                              "当前气血": 自己.当前气血,
                          }}, True)
    return True, f"使用大活血丹成功，当前气血为{自己.当前气血}"


async def 疏络丹(自己: UserInfo, 数量: int):
    if 自己.基础属性["重伤状态"]:
        return "重伤状态下无法使用"
    for _ in range(数量):
        自己.当前内力 += 500
    if 自己.当前内力 > 自己.当前状态["内力上限"]:
        自己.当前内力 = 自己.当前状态["内力上限"]
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                          {"$set": {
                              "当前内力": 自己.当前内力,
                          }}, True)
    return True, f"使用疏络丹成功，当前内力为{自己.当前内力}"


async def 大疏络丹(自己: UserInfo, 数量: int):
    if 自己.基础属性["重伤状态"]:
        return "重伤状态下无法使用"

    自己.当前内力 = 自己.当前状态["内力上限"]
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                          {"$set": {
                              "当前内力": 自己.当前内力,
                          }}, True)
    return True, f"使用大疏络丹成功，当前内力为{自己.当前内力}"


async def 大洗髓丹(自己: UserInfo, 数量: int):
    pass


async def _开宝箱(自己: UserInfo,
                 宝箱名称,
                 数量,
                 消耗精力,
                 装备概率,
                 银两概率,
                 银两下限,
                 银两上限,
                 材料概率,
                 材料等级,
                 材料数量下限,
                 材料数量上限,
                 图纸概率,
                 图纸等级下限,
                 图纸等级上限,
                 其他物品=[]):
    msg = ""
    user_id = 自己.基础属性["_id"]
    获得银两 = 0
    获得材料 = {}
    获得图纸 = {}
    获得物品 = {}
    共消耗精力 = 数量 * 消耗精力
    user_info = jianghu.user.find_one({"_id": user_id})
    现有精力 = user_info.get("精力", 0)
    if 现有精力 < 共消耗精力:
        return False, f"使用 {数量} 个{宝箱名称}需要{共消耗精力}点精力, 你目前只有{现有精力}"
    jianghu.user.update_one({"_id": user_id}, {"$inc": {"精力": -共消耗精力}})
    for _ in range(数量):
        装备池 = list(
            jianghu.equip.find({"持有人": -2}, projection={
                "装备分数": 1,
                "镶嵌分数": 1
            }))
        if 装备概率 < random.randint(0, len(装备池)):
            装备 = random.choice(装备池)
            装备名称 = 装备["_id"]
            装备分数 = 装备.get("装备分数", 0) + 装备.get("镶嵌分数", 0)
            jianghu.equip.update_one({"_id": 装备名称}, {"$set": {"持有人": user_id}})
            msg += f"\n装备【{装备名称}】({装备分数})"
        if random.randint(1, 100) < 银两概率:
            获得银两 += random.randint(银两下限, 银两上限)
        if random.randint(1, 100) < 材料概率:
            材料属性 = random.choice("金木水火土")
            材料名称 = f"{材料等级}{材料属性}"
            材料数量 = random.randint(材料数量下限, 材料数量上限)
            if 材料名称 not in 获得材料:
                获得材料[材料名称] = 0
            获得材料[材料名称] += 材料数量
        if random.randint(1, 100) < 图纸概率:
            图纸属性 = random.choice(["武器", "饰品", "外装"])
            图纸等级 = random.randint(图纸等级下限, 图纸等级上限)
            图纸名称 = f"{图纸属性}{图纸等级}"
            if 图纸名称 not in 获得图纸:
                获得图纸[图纸名称] = 0
            获得图纸[图纸名称] += 1
        for 物品 in 其他物品:
            if 物品["概率"] > random.randint(0, 100):
                物品数量 = random.randint(*物品["数量"])
                物品名称 = 物品["名称"]
                if 物品名称 not in 获得物品:
                    获得物品[物品名称] = 0
                获得物品[物品名称] += 物品数量
    if 获得银两:
        msg += f"\n{获得银两}两银子"
        await 增加银两(user_id, 获得银两, f"使用{宝箱名称}")
    if 获得材料 or 获得图纸:
        背包 = jianghu.knapsack.find_one({"_id": user_id})
        图纸 = 背包.get("图纸", {})
        材料 = 背包.get("材料", {})
        if 获得材料:
            for k, v in 获得材料.items():
                if k not in 材料:
                    材料[k] = 0
                材料[k] += v
                msg += f"\n{k}*{v}"
        if 获得图纸:
            for k, v in 获得图纸.items():
                if k not in 图纸:
                    图纸[k] = 0
                图纸[k] += v
                msg += f"\n{k}*{v}"
        jianghu.knapsack.update_one({"_id": user_id},
                               {"$set": {
                                   "图纸": 图纸,
                                   "材料": 材料
                               }})
    if 获得物品:
        jianghu.knapsack.update_one({"_id": user_id}, {"$inc": 获得物品})
        msg += "\n"+"\n".join([f"{k}*{v}" for k, v in 获得物品.items()])

    if msg:
        msg = f"消耗{共消耗精力}点精力, 打开了{数量}个{宝箱名称}, 获得:" + msg
    else:
        msg = f"消耗{共消耗精力}点精力, 你啥都没开出来"
    return True, msg


async def 青铜宝箱(自己: UserInfo, 数量: int):
    data = {
        "自己": 自己,
        "宝箱名称": "青铜宝箱",
        "数量": 数量,
        "消耗精力": 0,
        "装备概率": 80,
        "银两概率": 90,
        "银两下限": 800,
        "银两上限": 2000,
        "材料概率": 8,
        "材料等级": "青",
        "材料数量下限": 4,
        "材料数量上限": 11,
        "图纸概率": 8,
        "图纸等级下限": 200,
        "图纸等级上限": 260,
        "其他物品": [{"名称": "精力丹", "概率": 3, "数量": (1, 2)}]
    }
    return await _开宝箱(**data)


async def 精铁宝箱(自己: UserInfo, 数量: int):
    data = {
        "自己": 自己,
        "宝箱名称": "精铁宝箱",
        "数量": 数量,
        "消耗精力": 1,
        "装备概率": 60,
        "银两概率": 90,
        "银两下限": 1000,
        "银两上限": 4000,
        "材料概率": 10,
        "材料等级": "蓝",
        "材料数量下限": 3,
        "材料数量上限": 9,
        "图纸概率": 10,
        "图纸等级下限": 220,
        "图纸等级上限": 280,
        "其他物品": [{"名称": "精力丹", "概率": 10, "数量": (1, 3)}]
    }
    return await _开宝箱(**data)


async def 素银宝箱(自己: UserInfo, 数量: int):
    data = {
        "自己": 自己,
        "宝箱名称": "素银宝箱",
        "消耗精力": 2,
        "数量": 数量,
        "装备概率": 40,
        "银两概率": 90,
        "银两下限": 3000,
        "银两上限": 6000,
        "材料概率": 12,
        "材料等级": "紫",
        "材料数量下限": 2,
        "材料数量上限": 8,
        "图纸概率": 12,
        "图纸等级下限": 240,
        "图纸等级上限": 300,
        "其他物品": [
            {"名称": "精力丹", "概率": 15, "数量": (1, 4)},
            {"名称": "功德录", "概率": 5, "数量": (1, 3)},
        ]
    }
    return await _开宝箱(**data)


async def 鎏金宝箱(自己: UserInfo, 数量: int):
    data = {
        "自己": 自己,
        "宝箱名称": "鎏金宝箱",
        "消耗精力": 3,
        "数量": 数量,
        "装备概率": 20,
        "银两概率": 90,
        "银两下限": 5000,
        "银两上限": 8000,
        "材料概率": 14,
        "材料等级": "彩",
        "材料数量下限": 1,
        "材料数量上限": 5,
        "图纸概率": 14,
        "图纸等级下限": 260,
        "图纸等级上限": 330,
        "其他物品": [
            {"名称": "精力丹", "概率": 18, "数量": (1, 4)},
            {"名称": "功德录", "概率": 10, "数量": (3, 5)},
        ]
    }
    return await _开宝箱(**data)


async def 福禄宝箱(自己: UserInfo, 数量: int):
    data = {
        "自己": 自己,
        "宝箱名称": "福禄宝箱",
        "数量": 数量,
        "装备概率": 5,
        "银两概率": 90,
        "银两下限": 10000,
        "银两上限": 20000,
        "材料概率": 50,
        "材料等级": "彩",
        "材料数量下限": 3,
        "材料数量上限": 7,
        "图纸概率": 50,
        "图纸等级下限": 300,
        "图纸等级上限": 350,
        "其他物品": [
            {"名称": "老君手书", "概率": 1, "数量": (1, 1)},
        ]
    }
    return await _开宝箱(**data)


async def 精力丹(自己: UserInfo, 数量: int):
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                            {"$inc": {
                                "精力": 数量 * 10,
                            }}, True)
    return True, f"使用精力丹成功，恢复精力{数量 * 10}点"


async def 功德录(自己: UserInfo, 数量: int):
    增加善恶 = 数量 * 5
    if 自己.基础属性["善恶值"] >= 95:
        return False, f"你的善恶值不需要用!"
    if 自己.基础属性["善恶值"] + 增加善恶 > 100:
        return False, f"你的善恶值没那么低，现在只能使用{(100 - 自己.基础属性['善恶值']) // 5}本"
    jianghu.user.update_one({"_id": 自己.基础属性["_id"]},
                          {"$inc": {"善恶值": 增加善恶}}, True)
    return True, f"使用功德录成功，善恶值+{增加善恶}"


async def 洗髓丹体质(自己: UserInfo, 数量: int):
    pass


async def 洗髓丹力道(自己: UserInfo, 数量: int):
    pass


async def 洗髓丹元气(自己: UserInfo):
    pass


async def 洗髓丹根骨(自己: UserInfo):
    pass


async def 洗髓丹身法(自己: UserInfo):
    pass


async def 人傻钱多(自己: UserInfo):
    return True, "这个东西价值一个亿，真有钱啊，一个亿。整整一亿银两。真有钱。"


shop = {
    "人傻钱多": {
        "价格": 100000000,
        "使用": 人傻钱多,
        "使用数量": 1
    },
    "材料盒": {
        "价格": 10,
        "使用": 材料盒,
        "使用数量": 10000000
    },
    "图纸盒": {
        "价格": 10,
        "使用": 图纸盒,
        "使用数量": 10000000
    },
    "活血丹": {
        "使用": 活血丹,
        "使用数量": 10
    },
    "大活血丹": {
        "使用": 大活血丹,
        "使用数量": 1
    },
    "疏络丹": {
        "使用": 疏络丹,
        "使用数量": 10
    },
    "大疏络丹": {
        "使用": 大疏络丹,
        "使用数量": 1
    },
    "青铜宝箱": {
        "使用": 青铜宝箱,
        "使用数量": 100
    },
    "精铁宝箱": {
        "使用": 精铁宝箱,
        "使用数量": 100
    },
    "素银宝箱": {
        "使用": 素银宝箱,
        "使用数量": 100
    },
    "鎏金宝箱": {
        "使用": 鎏金宝箱,
        "使用数量": 100
    },
    "福禄宝箱": {
        "使用": 福禄宝箱,
        "使用数量": 100
    },
    "精力丹": {
        "使用": 精力丹,
        "使用数量": 100
    },
    "功德录": {
        "使用": 功德录,
        "使用数量": 100
    }
    # "大洗髓丹": {
    #     "价格": 5000,
    #     "使用": 大洗髓丹,
    #     "使用数量": 1
    # },
    # "洗髓丹体质": {
    #     "价格": 150,
    #     "使用": 洗髓丹体质,
    #     "使用数量": 5
    # },
    # "洗髓丹力道": {
    #     "价格": 150,
    #     "使用": 洗髓丹力道,
    #     "使用数量": 5
    # },
    # "洗髓丹元气": {
    #     "价格": 150,
    #     "使用": 洗髓丹元气,
    #     "使用数量": 5
    # },
    # "洗髓丹根骨": {
    #     "价格": 150,
    #     "使用": 洗髓丹根骨,
    #     "使用数量": 5
    # },
    # "洗髓丹身法": {
    #     "价格": 150,
    #     "使用": 洗髓丹身法,
    #     "使用数量": 5
    # }
}
