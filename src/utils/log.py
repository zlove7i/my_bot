from datetime import datetime
from src.utils.db import db

logs = db.client["logs"]

DEBUG = 1
INFO = 2
WARN = 3
ERROR = 4


class Log(object):

    def debug(self, msg: str):
        now = datetime.now()
        log = logs[now.strftime("bot-%Y-%m")]
        log.insert_one({
            "msg": msg,
            "level": DEBUG,
            "time": now
        })
        print(f'{now.strftime("%m-%d %H:%M:%S")} [DEBUG] {msg}')

    def info(self, msg: str):
        now = datetime.now()
        log = logs[now.strftime("bot-%Y-%m")]
        log.insert_one({
            "msg": msg,
            "level": INFO,
            "time": now
        })
        print(f'{now.strftime("%m-%d %H:%M:%S")} [INFO] {msg}')

    def warning(self, msg: str):
        now = datetime.now()
        log = logs[now.strftime("bot-%Y-%m")]
        log.insert_one({
            "msg": msg,
            "level": WARN,
            "time": now
        })
        print(f'{now.strftime("%m-%d %H:%M:%S")} [WARNING] {msg}')

    def error(self, msg: str):
        now = datetime.now()
        log = logs[now.strftime("bot-%Y-%m")]
        log.insert_one({
            "msg": msg,
            "level": ERROR,
            "time": now
        })
        print(f'{now.strftime("%m-%d %H:%M:%S")} [ERROR] {msg}')


logger = Log()
