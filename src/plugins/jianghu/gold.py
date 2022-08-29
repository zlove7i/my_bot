from src.utils.db import db
from src.utils.log import logger

async def 记录(user_id, 项目, 数额, 余额):
    logger.info(f'银两变动 | {备注} | {user_id} | {金额}')
    return 

async def 查询银两(user_id):
    user = db.user_info.find_one({'_id': user_id})
    return user.get("gold", 0) if user else 0


async def 减少银两(user_id, 金额, 备注: str = ""):
    余额 = await 查询银两(user_id)
    if 余额 < 金额:
        return False
    db.user_info.update_one(
        {"_id": user_id},
        {"$inc": {"gold": -金额}}
    )
    await 记录(user_id, 备注, -金额, 余额 - 金额)
    return True


async def 增加银两(user_id, 金额, 备注: str = ""):
    余额 = await 查询银两(user_id)
    db.user_info.update_one(
        {"_id": user_id},
        {"$inc": {"gold": 金额}}
    )
    await 记录(user_id, 备注, 金额, 余额 + 金额)
    return True


async def 赠送银两(user_id, 被赠送, 金额):
    logger.info(f'赠送银两 {user_id} -> {被赠送} {金额}')
    if await 减少银两(user_id, 金额, f"送给{被赠送}"):
        await 增加银两(被赠送, 金额, f"{user_id}赠送")
        return True
    logger.info(f'赠送银两 {user_id} -> {被赠送} {金额} 失败')
    return False
