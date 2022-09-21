from pydantic import BaseModel

from fastapi import Depends, APIRouter

from src.router.auth import authenticate_user, register, send_verification_code
from src.router.manage import get_bot_list, manipulate_bot, ManipulateBot


router = APIRouter()





class RegisterItem(BaseModel):
    username: str
    password: str
    verifycode: str


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
