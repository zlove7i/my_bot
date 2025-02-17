from nonebot import on_regex
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher, Bot
from nonebot.message import run_preprocessor
from src.utils.permission import BOT_MASTER, SUPER_MANAGER
from src.utils.black_list import check_black_list

from . import data_source as source


@run_preprocessor
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    '''插件管理系统，插件开关实现'''
    bot_id = int(bot.self_id)
    if not await source.get_bot_enable(bot_id):
        raise IgnoredException("机器人注册")
    # 检测插件是否注册
    group_id = event.group_id
    user_id = event.user_id
    is_user_black, _ = await check_black_list(user_id, "QQ")
    is_group_black, _ = await check_black_list(group_id, "群号")
    if is_group_black:
        raise IgnoredException()
    module_name = matcher.plugin_name
    status = await source.get_plugin_status(group_id, module_name)
    if not status:
        # 停止未开启的插件
        raise IgnoredException("插件未开启")

    if event.get_plaintext() in ["闭嘴", "说话", "菜单"]:
        return
    # 检测机器人总开关
    bot_status = await source.get_bot_status(group_id)
    if (not bot_status or is_user_black):
        raise IgnoredException("机器人未开启")


# ----------------------------------------------------------------------------
#   插件开关指令管理，开关有2层：
#   第一层：群ws接收消息开关和各类设置开关
#   第二层：plugins插件开关
#   2层通用一个“打开|关闭 [name]”指令，所以要做2次判断，目前通过优先级来传递
# -----------------------------------------------------------------------------
regex = r"^(打开|关闭) [\u4e00-\u9fa5]+$"
group_status = on_regex(pattern=regex,
                        permission=BOT_MASTER | SUPER_MANAGER | GROUP_ADMIN | GROUP_OWNER,
                        priority=2,
                        block=False)  # 群设置

plugin_status = on_regex(pattern=regex,
                         permission=BOT_MASTER | SUPER_MANAGER | GROUP_ADMIN | GROUP_OWNER,
                         priority=3,
                         block=True)  # 插件设置


@group_status.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    '''群设置开关'''
    get_msg = event.get_plaintext().split(" ")
    status = get_msg[0]
    config_type = get_msg[-1]
    if config_type not in ["进群通知", "离群通知", "开服推送", "新闻推送"]:
        await group_status.finish()
    flag = await source.change_group_config(event.group_id, config_type,
                                            status)
    if flag:
        matcher.stop_propagation()
        await group_status.finish(f"设置成功！\n[{config_type}]当前已 {status}")
    await group_status.finish()


@plugin_status.handle()
async def _(event: GroupMessageEvent):
    '''设置插件开关'''
    get_msg = event.get_plaintext().split(" ")
    status = get_msg[0]
    plugin_name = get_msg[-1]
    flag = await source.change_plugin_status(event.group_id, plugin_name,
                                             status)
    if flag:
        msg = f"设置成功！\n插件[{plugin_name}]当前已 {status}"
    else:
        msg = f"设置失败！未找到插件[{plugin_name}]"
    await plugin_status.finish(msg)
