import random
from datetime import datetime

from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from src.utils.db import jianghu, my_bot
from src.utils.log import logger
from src.utils.browser import browser
from .zhouyi import suangua

client = AsyncClient()
'''异步请求客户端'''


async def get_sign_in(user_id: int, user_name: str, group_id: int) -> Message:
    '''
    :说明
        用户签到

    :参数
        * user_id：用户QQ
        * group_id：QQ群号

    :返回
        * Message：机器人返回消息
    '''
    gold = 0
    if _con := jianghu.user.find_one({'_id': user_id}):
        if _con.get("是否签到"):
            logger.debug(f"群({group_id}) | {user_id} | 重复签到")
            msg = MessageSegment.text('每天只能签到一次，签到次数会在 8:00 重置')
            return msg
        gold = _con.get("银两", 0)
    suangua_data = suangua()
    prize_pools = my_bot.bot_conf.find_one({'_id': 1})
    if not prize_pools:
        prize_pools = {}
    prize_pool = prize_pools.get("prize_pool", 0)
    if prize_pool < 1000000:
        prize_pool = 1000000
    get_gold_num = random.randint(10, prize_pool // 1000)
    gold += get_gold_num
    my_bot.bot_conf.update_one({'_id': 1},
                               {'$inc': {
                                   "prize_pool": -get_gold_num,
                               }}, True)
    energy = random.randint(10, 30)
    jianghu.user.update_one({'_id': user_id}, {
        "$inc": {
            "银两": get_gold_num,
            "精力": energy,
        },
        '$set': {
            "签到时间": datetime.now(),
            "是否签到": True,
            "卦": suangua_data
        }
    }, True)

    # 签到名次
    my_bot.bot_conf.update_one({'_id': 1}, {'$inc': {"sign_num": 1}}, True)
    sign_num = my_bot.bot_conf.find_one({'_id': 1}).get("sign_num", 0)
    logger.debug(f"群({group_id}) | {user_id} | 签到成功")
    pagename = "签到.html"
    img = await browser.template_to_image(user_name=user_name,
                                          user_id=user_id,
                                          pagename=pagename,
                                          sign_num=sign_num,
                                          get_gold_num=get_gold_num,
                                          gold=gold,
                                          energy=energy,
                                          **suangua_data)
    return MessageSegment.image(img)
