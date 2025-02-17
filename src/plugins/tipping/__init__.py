import os
from nonebot import export, on_regex
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP
from src.utils.browser import browser
from src.utils.log import logger


Export = export()
Export.plugin_name = "投喂"
Export.plugin_command = "投喂"
Export.plugin_usage = "钱多的老爷可以投喂，但是不会获得任何收益"
Export.default_status = True

tipping = on_regex(r"^(投喂|打赏)$", permission=GROUP, priority=1, block=True)


@tipping.handle()
async def _(event: GroupMessageEvent):
    '''投喂'''
    user_id = event.user_id
    group_id = event.group_id
    user_name = event.sender.nickname
    logger.info(f"群{group_id} | {user_name}({user_id}) | 投喂")
    pagename = "投喂.html"
    img = await browser.template_to_image(pagename=pagename)
    await tipping.finish(MessageSegment.image(img))
