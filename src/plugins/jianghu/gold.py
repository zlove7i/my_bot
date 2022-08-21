from src.utils.db import db
from src.utils.log import logger


async def 查询银两(user_id):
    user = db.user_info.find_one({'_id': user_id})
    return user.get("gold", 0) if user else 0


async def 减少银两(user_id, 金额, 备注: str = ""):
    if await 查询银两(user_id) < 金额:
        logger.info(f'减少银两 | {备注} | {user_id} | {金额} | 失败, 银两不足')
        return False
    db.user_info.update_one(
        {"_id": user_id},
        {"$inc": {"gold": -金额}}
    )
    logger.info(f'减少银两 | {备注} | {user_id} | {金额} | 成功')
    return True


async def 增加银两(user_id, 金额, 备注: str = ""):
    db.user_info.update_one(
        {"_id": user_id},
        {"$inc": {"gold": 金额}}
    )
    logger.info(f'增加银两 | {备注} | {user_id} | {金额} | 成功')
    return True


async def 赠送银两(user_id, 赠送者, 金额):
    logger.info(f'赠送银两 {user_id} -> {赠送者} {金额}')
    if await 减少银两(赠送者, 金额):
        await 增加银两(user_id, 金额)
        logger.info(f'赠送银两 {user_id} -> {赠送者} {金额} 成功')
        return True
    logger.info(f'赠送银两 {user_id} -> {赠送者} {金额} 失败')
    return False
