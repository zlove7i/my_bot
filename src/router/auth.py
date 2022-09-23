from datetime import datetime, timedelta
from typing import Union

from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from src.router.db_api import db_api
from src.utils.email import mail_client
from src.utils.regex import re_mail, re_password
from src.utils.config import config


SECRET_KEY = config.node_info['secret_key']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60


class Token(BaseModel):
    access_token: str
    token_type: str
    code: int


class Register(BaseModel):
    username: Union[str, None] = None
    password: Union[str, None] = None


class User(BaseModel):
    username: str
    password: str
    user_permission: int

    def check_permission(self, permission=5):
        if self.user_permission < permission:
            return False
        return True


class RegisterItem(BaseModel):
    username: str
    password: str
    verifycode: str


class LoginItem(BaseModel):
    username: str
    password: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def authenticate_user(login_item: LoginItem):
    check_result, msg = db_api.verify_user(login_item.username,
                                           login_item.password)
    if not check_result:
        return {"code": 400, 'msg': msg}
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {
        "username": login_item.username,
        "exp": datetime.utcnow() + access_token_expires
    }
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return {
        'code': 200,
        'msg': "登录成功！",
        'data': {
            "token_type": "bearer",
            'token': encoded_jwt,
            'user_permission': msg,
            'username': login_item.username
        }
    }


async def add_user(register_item: RegisterItem):
    if not re_mail.search(register_item.username):
        raise Exception("用户名格式错误, 请重新输入")
    if not re_password.search(register_item.password):
        raise Exception("密码格式错误, 请重新输入")
    return db_api.add_user(register_item)


async def get_current_user(requst: Request):
    try:
        token = requst.headers.get("authorization", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            return {}
    except JWTError:
        return {}
    user = db_api.get_user_info(username)
    user["username"] = user["_id"]
    if not user:
        return {}
    return User(**dict(user))


async def register(register_item: RegisterItem):
    if not re_mail.search(register_item.username):
        return {"code": 400, "msg": "用户名格式错误, 请重新输入"}
    if not re_password.search(register_item.password):
        return {"code": 400, "msg": "密码格式错误, 请重新输入"}
    return db_api.add_user(register_item)


async def send_verification_code(user: str):
    try:
        if not re_mail.search(user):
            raise Exception("用户名格式错误, 请重新输入")
        check_result, msg = db_api.create_verification_code(user)
        if check_result == 200:
            await mail_client.send_mail(
                user, "二猫子发给你的验证码",
                f"<h1>{msg}</h1><br>上面是你的验证码，记得保护好自己，不要把验证码发给别人")
            return {'code': check_result, 'msg': "验证码发送成功"}
        else:
            return {'code': check_result, 'msg': msg}
    except Exception as err:
        return {'code': 400, 'msg': str(err)}
