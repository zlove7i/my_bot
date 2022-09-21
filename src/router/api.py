from fastapi import Depends, APIRouter

from src.router.auth import authenticate_user, register, send_verification_code
from src.router.bot import get_bot_list, manipulate_bot
from src.router.chat_log import get_chat_log
from src.router.black_list import get_black_list, set_black_list


router = APIRouter()


@router.post("/api/login")
async def login_for_access_token(data: dict = Depends(authenticate_user)):
    return data


@router.post("/api/register")
async def register_user(data: dict = Depends(register)):
    return data


@router.get("/api/register")
async def send_verification(data: dict = Depends(send_verification_code)):
    return data


@router.get("/api/get_bot_list")
async def api_get_bot_list(data: dict = Depends(get_bot_list)):
    return data


@router.post("/api/manipulate_bot")
async def api_manipulate_bot(data: dict = Depends(manipulate_bot)):
    return data


@router.get("/api/get_chat_log")
async def api_get_chat_log(data: dict = Depends(get_chat_log)):
    return data


@router.get("/api/black_list")
async def api_get_black_list(data: dict = Depends(get_black_list)):
    return data


@router.post("/api/black_list")
async def api_set_black_list(data: dict = Depends(set_black_list)):
    return data
