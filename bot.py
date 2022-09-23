#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

from src.utils.moinkeypath import monkeypatch
from src.utils.scheduler import start_scheduler
from fastapi.middleware.cors import CORSMiddleware
from src.router.api import router


import time
from fastapi import Request


# 猴子补丁，针对windows平台，更换事件循环
monkeypatch()
nonebot.init()
app = nonebot.get_asgi()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(router)

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 开启定时器
driver.on_startup(start_scheduler)

# 加载管理插件
nonebot.load_plugins("src/managers")
# 加载其他插件
nonebot.load_plugins("src/plugins")


if __name__ == "__main__":
    nonebot.run()
