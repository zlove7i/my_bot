import datetime

from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from src.utils.cooldown_time import search_record, search_once
from src.utils.db import my_bot
from src.utils.log import logger
from src.utils.browser import browser
from src.utils.email import mail_client

client = AsyncClient()
'''异步请求客户端'''


async def sent_river_lantern(
    user_id: int,
    user_name: str,
    类型: str,
    content: str,
) -> Message:
    '''
    :说明
        放河灯

    :参数
        * user_id：用户QQ
        * content：河灯内容
        * user_name：用户名

    :返回
        * Message：机器人返回消息
    '''
    app_name = "放河灯"
    # 查看冷却时间
    n_cd_time = 60
    flag, cd_time = await search_record(user_id, app_name, n_cd_time)
    if not flag:
        msg = f"[{app_name}] 冷却 > [{cd_time}]"
        return msg

    if 类型 == "回复河灯":
        河灯id, content = content
        con = my_bot.river_lantern.find_one({"_id": int(河灯id)})
        if not con:
            return "找不到你要回复的河灯"
        回复内容 = con["content"]
        回复昵称 = con["user_name"]
        你的回复 = content
        content += f"//{回复昵称}：{回复内容}"
        if len(content) > 512:
            content = "//".join(content[:512].split("//")[:-1])

    await search_once(user_id, app_name)
    content = content.strip()
    insert_data = {
        'user_id': user_id,
        "content": content,
        "last_sent": datetime.datetime.today()
    }
    if user_name:
        insert_data.update({"user_name": user_name})
    # 记录投放
    编号 = my_bot.insert_auto_increment("river_lantern", insert_data)
    msg = f"{user_name}，河灯{编号}帮你放好了"

    if 类型 == "回复河灯":
        回复user_id = con["user_id"]
        邮件内容 = f"您的河灯{河灯id}收到了【{user_name}】的回复！\n" \
                  f"回复内容：{你的回复}\n\n" \
                  f"原内容：{回复内容}\n\n" \
                  f"如果想要回复这个河灯可以在任意群发送“回复河灯 {编号} 你的内容”"
        await mail_client.send_mail(回复user_id, "河灯回复通知", 邮件内容)
    logger.debug(f"{user_id} | 投放成功！ | {content}")

    return msg


async def get_river_lantern(group_id, user_id) -> Message:
    '''捡一盏三天内的河灯'''
    # 查看冷却时间
    n_cd_time = 3
    app_name = "捡河灯"
    flag, cd_time = await search_record(user_id, app_name, n_cd_time)
    if not flag:
        msg = f"[{app_name}] 冷却 > [{cd_time}]"
        return msg
    # 记录一次查询
    await search_once(user_id, app_name)
    plugins_info = my_bot.plugins_info.find_one({"_id": group_id})
    status = True
    if plugins_info:
        status = plugins_info.get("river_lantern", {}).get("status", True)
    if not status:
        return "本群已关闭河灯功能，如果要恢复，请发送“打开 河灯”"

    con_list = list(my_bot.river_lantern.aggregate([{"$sample": {"size": 1}}]))
    if not con_list:
        logger.debug("无河灯")
        return "现在找不到河灯。"

    con = con_list[0]
    lantern_id = con.get("_id")
    content = con.get("content")
    user_name = con.get("user_name")
    if not content:
        logger.debug("空河灯")
        return "你捡到了一个空的河灯。要不你来放一个？"
    my_bot.river_lantern.update_one({"_id": lantern_id},
                                {"$inc": {
                                    "views_num": 1
                                }})
    logger.debug(f"河灯 | {content}")
    if isinstance(lantern_id, int):
        msg = f"花笺{lantern_id}：\n    {content}"
    else:
        msg = f"花笺：\n    {content}"
    if user_name:
        msg = f"{user_name}的" + msg
    return msg


async def my_river_lantern(user_id: int, user_name: str):
    '''查看自己的所有河灯'''
    filter = {'user_id': user_id}
    sort = list({'last_sent': -1}.items())
    limit = 10
    con = my_bot.river_lantern.find(filter=filter, sort=sort, limit=limit)
    data = list(con)
    if not data:
        return "你还没投放过河灯。"
    datas = []
    index_num = 0
    for i in data:
        index_num += 1
        content = i["content"]
        datas.append({
            "index_num":
            index_num,
            "content":
            content,
            "datetime":
            i["last_sent"].strftime("%Y-%m-%d %H:%M:%S"),
            "views_num":
            i.get("views_num", 0)
        })

    logger.debug(f"{user_id} | 查看河灯")
    pagename = "./河灯/查看河灯.html"
    img = await browser.template_to_image(user_name=user_name,
                                          user_id=user_id,
                                          pagename=pagename,
                                          datas=datas)
    return MessageSegment.image(img)
