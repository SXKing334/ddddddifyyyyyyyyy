# novel\infrastructure\redis\client.py

import redis.asyncio as redis
from redis.asyncio import ConnectionPool


from novel.exception.exceptions import RedisConnectionException


class RedisClientFactory:
    """
    Redis 客户端工厂类
    负责管理连接池和客户端实例的生命周期
    """
    _pool: ConnectionPool | None = None
    _client: redis.Redis | None = None

    @classmethod
    async def init_pool(cls, host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None):
        """
        初始化连接池（通常在应用启动时调用）
        """
        if cls._pool is None:
            cls._pool = ConnectionPool.from_url(
                f"redis://{host}:{port}/{db}",
                password=password,
                max_connections=20,    # 连接池最大连接数
                decode_responses=True  # 自动解码为 str，否则返回 bytes
            )
            # 创建客户端实例
            cls._client = redis.Redis(connection_pool=cls._pool)
            try:
                await cls._client.ping()
            except redis.ConnectionError:
                raise RedisConnectionException("❌ Redis 连接失败，请检查服务是否启动！")

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        获取 Redis 客户端实例
        注意：这里不需要 await，直接返回已初始化的客户端
        """
        if cls._client is None:
            raise RuntimeError("Redis 连接池尚未初始化，请先调用 init_pool")
        return cls._client

    @classmethod
    async def close(cls):
        """
        关闭连接池（通常在应用关闭时调用）
        """
        if cls._pool:
            await cls._client.close()
            await cls._pool.disconnect()
            cls._pool = None
            cls._client = None
            print("✅ Redis 连接池已关闭")


# --- 简单的测试脚本 ---
import asyncio
async def main():
    # 1. 初始化
    await RedisClientFactory.init_pool()

    # 2. 获取客户端
    client = RedisClientFactory.get_client()

    # 3. 执行操作
    await client.set("foo", "bar")
    val = await client.get("foo")
    print(f"🔍 从 Redis 读取: {val}")

    # 4. 关闭
    await RedisClientFactory.close()
if __name__ == "__main__":
    asyncio.run(main())