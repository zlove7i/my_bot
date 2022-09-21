#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

from src.utils.moinkeypath import monkeypatch
from src.utils.scheduler import start_scheduler
from fastapi.middleware.cors import CORSMiddleware
from src.router import api, auth


import time
# import uvicorn
from fastapi import Request, Response
import json
# app = FastAPI()


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
    # result, msg = await auth.auth(request)
    # if not result:
    #     response = Response(content=json.dumps({"code": 400, "msg": msg}),
    #                         media_type="application/json",
    #                         status_code=404)
    #     return response
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(api.router)

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 开启定时器
driver.on_startup(start_scheduler)

# 加载管理插件
nonebot.load_plugins("src/managers")
# 加载其他插件
nonebot.load_plugins("src/plugins")

app.include_router(api.router)

if __name__ == "__main__":
    nonebot.run()


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8899)