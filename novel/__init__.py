import os
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from novel.controllers.index_page import index_router
from novel.controllers.public_page import public_router

from novel.core.config.setting import Setting

from novel.infrastructure.db.engine import async_engine
from novel.infrastructure.db.base import Base
from novel.infrastructure.redis.client import RedisClientFactory



def get_app() -> FastAPI:
    # 1、配置
    # 数据库配置：MySQL, Redis
    # 消息队列配置: MQ
    setting = Setting()



    # 2、生命周期
    @asynccontextmanager
    async def lifespan(app: FastAPI):

        # sqlalchemy(业务)
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # aiomysql(langgraph)

        # Redis
        await RedisClientFactory.init_pool()

        # MQ


        # 初始化全局对象
        print("lifespan：初始化全局变量实例")


        # 程序运行中
        print("✅ 服务启动成功")
        yield

        # 销毁全局对象


        print("🛑 服务关闭")


    # 3、FastAPI 实例
    app = FastAPI(
        title="LangGraph",
        description="LangGraph",
        version="0.1.0",
        docs_url="/docs" if os.environ.get("ENV") == "dev" else None,
        redoc_url="/redoc" if os.environ.get("ENV") == "dev" else None,
        openapi_url="/openapi.json" if os.environ.get("ENV") == "dev" else None,
        lifespan=lifespan
    )

    # 4、中间件
    #@app.middleware("http")
    #async def authenticate(
    #        request: Request,
    #        call_next: Callable[[Request], Awaitable[Response]]
    #):
    #    # 测试路由
#
    #    # 公共路由
#
    #    # token 密钥
#
    #    # 验证
#
    #    # 通行
    #    return await call_next(request)


    # 5、CORS: 跨域配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产应限制为具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 6、路由
    app.include_router(public_router)
    app.include_router(index_router)

    # 7、return FastAPI
    return app