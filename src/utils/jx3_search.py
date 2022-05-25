from typing import Optional, Tuple

from httpx import AsyncClient
from src.utils.cooldown_time import search_record, search_once
from src.utils.config import config
from src.utils.log import logger
from enum import Enum
from dataclasses import dataclass

@dataclass
class APP(object):
    '''jx3api的app类，关联url和cd时间'''
    url: str
    '''app的url'''
    cd: int
    '''app的cd时间'''


class JX3APP(Enum):
    '''jx3api的接口枚举'''
    日常任务 = APP("/app/daily", 0)
    开服检查 = APP("/app/check", 0)
    金价比例 = APP("/app/demon", 0)
    沙盘图片 = APP("/app/sand", 0)
    家园鲜花 = APP("/app/flower", 0)
    科举答题 = APP("/app/exam", 0)
    家园家具 = APP("/app/furniture", 0)
    查器物谱 = APP("/app/travel", 0)
    推荐小药 = APP("/app/heighten", 0)
    推荐装备 = APP("/app/equip", 0)
    推荐奇穴 = APP("/app/qixue", 0)
    查宏命令 = APP("/app/macro", 0)
    官方资讯 = APP("/app/news", 0)
    维护公告 = APP("/app/announce", 0)
    阵眼效果 = APP("/app/matrix", 0)
    物品价格 = APP("/app/price", 0)
    刷新地点 = APP("/app/horse", 0)
    主从大区 = APP("/app/server", 0)
    随机骚话 = APP("/app/random", 0)
    奇遇前置 = APP("/app/require", 0)
    奇遇攻略 = APP("/next/strategy", 0)
    奇遇查询 = APP("/next/serendipity", 10)
    奇遇统计 = APP("/next/statistical", 10)
    奇遇汇总 = APP("/next/collect", 10)
    资历排行 = APP("/next/seniority", 0)
    比赛战绩 = APP("/next/match", 10)
    战绩排行 = APP("/next/awesome", 10)
    战绩统计 = APP("/next/schools", 10)
    角色信息 = APP("/role/roleInfo", 0)
    装备属性 = APP("/role/attribute", 10)
    烟花记录 = APP("/role/secret", 10)

    加密计算 = APP("/token/calculate", 0)
    查有效值 = APP("/token/ticket", 0)
    到期查询 = APP("/token/socket", 0)


class TicketManager(object):
    '''ticket管理器类'''
    _client: AsyncClient
    '''异步请求客户端'''
    _check_url: str
    '''检测ticket有效性接口'''

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(TicketManager, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # 设置header
        self.token = config.jx3api['jx3_token']
        if self.token is None:
            self.token = ""
        self.headers = {"token": self.token, "User-Agent": "Nonebot2-jx3_bot"}
        self._client = AsyncClient(headers=self.headers)
        self._check_url = config.jx3api['jx3_url']+"/token/validity"

    async def check_ticket(self, ticket: str) -> bool:
        '''检查ticket的有效性'''
        params = {"ticket": ticket}
        try:
            req_url = await self._client.get(url=self._check_url, params=params)
            req = req_url.json()
            if req['code'] == 200:
                return True
            return False
        except Exception as e:
            logger.error(
                f"<r>查询ticket失败</r> | <g>{str(e)}</g>"
            )
            return False

    async def get_ticket(self) -> Optional[str]:
        '''获取一条有效的ticket，如果没有则返回None'''
        return "sdfsdg32322sfsdfsdf"


class SearchManager(object):
    '''查询管理器，负责查询记录和cd，负责搓app'''

    _main_site: str
    '''jx3api主站url'''

    def __init__(self):
        self._main_site = config.jx3api['jx3_url']

    def get_search_url(self, app: JX3APP) -> str:
        '''获取app请求地址'''
        return self._main_site+app.value.url

class Jx3Searcher(object):
    '''剑三查询类'''

    _client: AsyncClient
    '''异步请求客户端'''
    _search_manager = SearchManager()
    '''查询管理器'''

    def __new__(cls, *args, **kwargs):
        '''单例'''
        if not hasattr(cls, '_instance'):
            orig = super(Jx3Searcher, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # 设置header
        token = config.jx3api['jx3_token']
        if token is None:
            token = ""
        headers = {"token": token, "User-Agent": "Nonebot2-jx3_bot"}
        self._client = AsyncClient(headers=headers)

    async def get_server(self, server: str) -> Optional[str]:
        '''获取主服务器'''
        url = self._search_manager.get_search_url(JX3APP.主从大区)
        params = {"name": server}
        try:
            req = await self._client.get(url=url, params=params)
            req_json = req.json()
            msg = req_json['msg']
            if msg == "success":
                return req_json['data']['server']
            return None
        except Exception as e:
            logger.error(
                f"查询主从服务器失败，原因：{str(e)}"
            )
            return None

    async def get_data_from_api(self, group_id: int, app: JX3APP, params: dict) -> Tuple[str, dict]:
        '''
        :说明
            从jx3api获取数据
        :参数
            * group_id：QQ群号
            * app：app枚举
            * params：参数
        :返回
            * str：返回消息
            * dict：网站返回数据
        '''
        # 判断cd
        flag, cd_time = await search_record(group_id, app.name, app.value.cd)
        if not flag:
            logger.debug(
                f"<y>群{group_id}</y> | <g>{app.name}</g> | 冷却中：{cd_time}"
            )
            msg = f"[{app.name}]冷却中（{cd_time}）"
            return msg, {}

        # 记录一次查询
        await search_once(group_id, app.name)
        # 获取url
        url = self._search_manager.get_search_url(app)
        try:
            req = await self._client.get(url=url, params=params)
            req_json: dict = req.json()
            msg: str = req_json['msg']
            data = req_json['data']
            logger.debug(
                f"<y>群{group_id}</y> | <g>{app.name}</g> | 返回：{data}"
            )
            return msg, data
        except Exception as e:
            error = str(e)
            logger.error(
                f"<y>群{group_id}</y> | <g>{app.name}</g> | 失败：{error}"
            )
            return error, {}


ticket_manager = TicketManager()
'''ticket管理器'''

jx3_searcher = Jx3Searcher()
'''剑三查询器'''