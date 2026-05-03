# novel\infrastructure\redis\repo\workflow_repo.py
import json
from typing import Dict, Any

from redis.asyncio import Redis

from novel import RedisClientFactory


class WorkflowRedisRepo:
    KEY_WORKFLOW_INFO = "hope:workflow:info:{}:{}"   # tenant_id:workflow_id

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client


    async def set_workflow_info(
            self,
            tenant_id: int,
            workflow_id: int,
            workflow_data: Dict[str, Any],
            expire_seconds: int = 3600  # 默认1小时
    ) -> bool:
        """
        存储工作流信息到Redis
        :param tenant_id: 租户ID
        :param workflow_id: 工作流ID
        :param workflow_data: 工作流数据
        :param expire_seconds: 过期时间（秒）
        :return: 是否成功
        """
        key = self.KEY_WORKFLOW_INFO.format(tenant_id, workflow_id)
        value = json.dumps(workflow_data, default=str)
        await self.redis_client.setex(key, expire_seconds, value)
        return True

    async def get_workflow_info(
            self,
            tenant_id: int,
            workflow_id: int
    ) -> Dict[str, Any] | None:
        """
        获取工作流信息
        :param tenant_id: 租户ID
        :param workflow_id: 工作流ID
        :return: 工作流数据，不存在返回None
        """
        key = self.KEY_WORKFLOW_INFO.format(tenant_id, workflow_id)
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete_workflow_info(
            self,
            tenant_id: str,
            workflow_id: int
    ) -> bool:
        """
        删除工作流缓存
        :param tenant_id: 租户ID
        :param workflow_id: 工作流ID
        :return: 是否成功
        """
        key = self.KEY_WORKFLOW_INFO.format(tenant_id, workflow_id)
        await self.redis_client.delete(key)
        return True


def get_workflow_redis_repo() -> WorkflowRedisRepo:

    client = RedisClientFactory.get_client()

    return WorkflowRedisRepo(client)


