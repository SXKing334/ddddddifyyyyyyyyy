# novel\infrastructure\db\engine.py
import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from novel.exception.exceptions import SQLAlchemyEngineException, SQLAlchemySessionLocalException

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///database.db')
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://", 1)

# 1. 创建异步引擎
try:
    async_engine = create_async_engine(
        DATABASE_URL,
        pool_size=20,         # 连接池大小
        max_overflow=30,      # 最大溢出连接数
        pool_pre_ping=True,   # 每次取连接前检测是否存活
        pool_recycle=3600,    # 1小时自动回收连接
        echo=False            # 生产环境 False，开发调试建议 True
    )
except Exception as e:
    print(f"引擎初始化失败: {e}")
    raise SQLAlchemyEngineException(f"SQLAlchemy异步引擎初始化失败: {e}")



# 2. 创建异步会话工厂
try:
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False  # 异步模式下建议设为 False，防止访问已提交对象属性时报错
    )
except Exception as e:
    print(f"会话工厂创建失败: {e}")
    raise SQLAlchemySessionLocalException(f"SQLAlchemy异步会话工厂创建失败: {e}")

