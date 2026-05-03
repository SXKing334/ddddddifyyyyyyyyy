# novel\infrastructure\redis\repo\user_repo.py

import json
from typing import Dict

from redis.asyncio import Redis

from novel.infrastructure.redis.client import RedisClientFactory


class UserRedisRepository:
    # 1. 定义 Key 的命名规范 (集中管理，方便修改)
    KEY_USER_INFO = "hope:tenant:user:info:{}"                       # 存用户详情
    KEY_USER_REFRESH_TOKEN = "hope:tenant:user:refresh_token:{}"     # 刷新后的长token

    def __init__(self, redis_client: Redis):
        # 从工厂获取客户端实例
        self.redis = redis_client

    async def get_user_info(self, user_id: int) -> Dict | None:
        """
        获取用户信息
        业务层不需要知道数据是存成 JSON 还是 Hash，只需要拿字典
        """
        key = self.KEY_USER_INFO.format(user_id)

        # 自动反序列化
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    async def set_user_info(self, user_id: int, data: Dict, expire_seconds: int = 3600):
        """
        设置用户信息
        业务层只管传字典，仓库负责转 JSON 和 设置过期时间
        """
        key = self.KEY_USER_INFO.format(user_id)
        # 自动序列化
        await self.redis.set(key, json.dumps(data), ex=expire_seconds)
    async def delete_user_info(self, user_id: int):
        """删除用户信息"""
        key = self.KEY_USER_INFO.format(user_id)
        await self.redis.delete(key)

    async def get_user_refresh_token(self, user_id: int) -> str | None:
        """
        获取用户refresh_token
        """
        key = self.KEY_USER_REFRESH_TOKEN.format(user_id)
        data = await self.redis.get(key)
        if data:
            return data.decode() if isinstance(data, bytes) else data
        return None
    async def set_user_refresh_token(self, user_id: int, refresh_token: str, expire_seconds: int = 3600):
        """
        设置用户refresh_token
        """
        key = self.KEY_USER_REFRESH_TOKEN.format(user_id)
        await self.redis.set(key, refresh_token, ex=expire_seconds)
    async def delete_user_refresh_token(self, user_id: int):
        """删除refresh_token"""
        key = self.KEY_USER_REFRESH_TOKEN.format(user_id)
        await self.redis.delete(key)

    async def clear_user_session(self, user_id: int):
        """
        组合操作示例：删除用户信息的同时，也删除他的登录态
        """

        pipe = self.redis.pipeline(transaction=True)           # 使用 pipeline 批量操作，减少网络 RTT,开启事务
        pipe.delete(self.KEY_USER_INFO.format(user_id))
        pipe.delete(self.KEY_USER_SESSION.format(user_id))
        await pipe.execute()                                   # 推送


# 方便DI注入
def get_user_redis_repo() -> UserRedisRepository:
    # 复用同一个Redis连接池
    client = RedisClientFactory.get_client()
    # 返回Redis仓库
    return UserRedisRepository(client)