from src.utils.db import jianghu
from src.utils.log import logger


async def 记录(user_id, 项目, 数额, 余额, 目标=0):
    logger.info(f'银两变动 | {项目} | {user_id} | {数额}')
    return


async def 查询银两(user_id):
    user = jianghu.user.find_one({'_id': user_id})
    return user.get("银两", 0) if user else 0


async def 减少银两(user_id, 金额, 备注: str = "", 目标=0):
    余额 = await 查询银两(user_id)
    if 余额 < 金额:
        return False
    jianghu.user.update_one(
        {"_id": user_id},
        {"$inc": {"银两": -金额}}
    )
    await 记录(user_id, 备注, -金额, 余额 - 金额, 目标)
    return True


async def 增加银两(user_id, 金额, 备注: str = "", 目标=0):
    余额 = await 查询银两(user_id)
    jianghu.user.update_one(
        {"_id": user_id},
        {"$inc": {"银两": 金额}}
    )
    await 记录(user_id, 备注, 金额, 余额 + 金额, 目标)
    return True


async def 赠送银两(user_id, 被赠送, 金额):
    logger.info(f'赠送银两 {user_id} -> {被赠送} {金额}')
    if await 减少银两(user_id, 金额, f"赠送与", 被赠送):
        await 增加银两(被赠送, 金额, f"被赠送", user_id)
        return True
    logger.info(f'赠送银两 {user_id} -> {被赠送} {金额} 失败')
    return False
