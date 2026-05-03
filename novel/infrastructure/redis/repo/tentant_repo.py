# novel\infrastructure\redis\repo\tenant_repo.py

import json
from typing import Dict

from redis.asyncio import Redis

from novel.infrastructure.redis.client import RedisClientFactory


class TenantRedisRepository:
    # 1. 定义 Key 的命名规范
    # 建议用 ID 作为 Key 的后缀，因为 ID 是唯一且不可变的
    KEY_TENANT_INFO = "hope:tenant:info:{}"

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_tenant_info(self, tenant_id: int) -> Dict | None:
        """
        获取租户信息
        """
        key = self.KEY_TENANT_INFO.format(tenant_id)

        data = await self.redis.get(key)
        if data:
            # 自动反序列化
            return json.loads(data)
        return None
    async def set_tenant_info(self, tenant_id: int, data: Dict, expire_seconds: int = 3600):
        """
        设置租户信息
        通常租户信息变动不频繁，过期时间可以设长一点，或者根据业务需求调整
        """
        key = self.KEY_TENANT_INFO.format(tenant_id)
        # 自动序列化
        await self.redis.set(key, json.dumps(data), ex=expire_seconds)
    async def delete_tenant_info(self, tenant_id: int):
        """
        删除租户信息（当租户信息更新时调用）
        """
        key = self.KEY_TENANT_INFO.format(tenant_id)
        await self.redis.delete(key)
    async def clear_tenant_session(self, tenant_id: int):
        """
        组合操作示例：如果需要一次性清除租户相关的所有缓存
        """
        key = self.KEY_TENANT_INFO.format(tenant_id)
        await self.redis.delete(key)
        # 如果未来有其他 key，可以在这里加 pipe 批量删除


# 方便DI注入
def get_tenant_redis_repo() -> TenantRedisRepository:
    # 复用同一个Redis连接池
    redis_client = RedisClientFactory.get_client()
    # 返回Redis仓库
    return TenantRedisRepository(redis_client)



