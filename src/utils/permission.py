from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.permission import Permission
from src.utils.db import management, my_bot

async def _bot_maser(bot: Bot, event: Event) -> bool:
    """
    机器人的主人
    """
    bot_id = int(bot.self_id)
    user_id = int(event.user_id)
    return management.bot_info.find_one({"_id": bot_id}).get("master") == user_id

async def _super_manager(bot: Bot, event: Event) -> bool:
    """
    超级管理员
    """
    bot_id = int(bot.self_id)
    user_id = int(event.user_id)
    
    return user_id in my_bot.bot_conf.find_one({"_id": 1}).get("super_manage", [])

SUPER_MANAGER = Permission(_super_manager)
BOT_MASTER = Permission(_bot_maser)