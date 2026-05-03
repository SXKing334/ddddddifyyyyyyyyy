# novel\infrastructure\db\session.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from .engine import AsyncSessionLocal

# --- 方案 A：直接使用 SQLAlchemy 的原生能力 (推荐，最简洁) ---
# AsyncSessionLocal 本身就是个工厂，且支持 async with
# 用法: async with AsyncSessionLocal() as session: ...


# --- 方案 B：封装一层带异常处理的上下文 ---
@asynccontextmanager
async def get_db_session(commit_on_exit: bool = False) -> AsyncSession:
    """
    获取数据库会话的上下文管理器
    自动处理：获取连接、提交事务、回滚异常、关闭连接(归还池)
    """
    session = AsyncSessionLocal()
    try:
        yield session
        if commit_on_exit:
            await session.commit()     # 成功则提交
    except Exception as e:
        await session.rollback()       # 失败则回滚
        raise
    finally:
        await session.close()          # 会话归还连接到池

# 依赖注入函数 (专供 FastAPI Depends 使用)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session

            # 如果是增删改：service层记得commit
        finally:
            await session.close()