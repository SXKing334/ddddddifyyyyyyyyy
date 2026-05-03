import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from novel.infrastructure.db.session import get_db
from novel.infrastructure.redis.repo.user_repo import UserRedisRepository, get_user_redis_repo
from novel.service.tenant_service import TenantService
from novel.service.user_service import UserService
from novel.shared.schemas.public import  APIResponse

public_router = APIRouter(prefix='/api/public',tags=['无需身份验证的页面'])

class LoginRequest(BaseModel):
    tenant: str = Field(description="租户名")
    username: str = Field(description="用户名")
    password: str = Field(description="加密密码")

class TenantCreateRequest(BaseModel):
    # 租户信息
    name: str = Field(description="租户名")
    app_id: str = Field(description="租户唯一标识")
    secret: str = Field(description="调用API的密钥")
    plan: str = Field(default="free",description="订阅版本")
    quota_max_chats: int = Field(default=50,description="最大使用次数")
    created_at: datetime.datetime = Field(default=datetime.datetime.now(),description="创建时间")
    is_active: bool = Field(default=True,description="租户状态")

    # 初始管理员信息
    username: str = Field(description="管理员用户名")
    password: str = Field(description="管理员密码")




@public_router.post(path='/login',tags=['登录'])
async def login(
        login_request: LoginRequest,
        db: AsyncSession = Depends(get_db),
        user_service: UserService = Depends(UserService)
) -> APIResponse:
    # 1. 传递参数到service层进行处理获取结果
    response: APIResponse = await user_service.login(db, login_request)

    # 2. 数据库提交事务
    await db.commit()

    # 3. 返回结果
    return response

@public_router.post(path='/register', tags=['租户注册'])
async def register(
        tenant_register_request: TenantCreateRequest,
        db: AsyncSession = Depends(get_db),
        tenant_service: TenantService = Depends(TenantService)
) -> APIResponse:
    # 1. 传递参数service层进行处理获取结果
    response: APIResponse = await tenant_service.register(db, tenant_register_request)

    # 2.数据库提交事务
    await db.commit()

    # 3. 返回结果
    return response

@public_router.get(path='/logout',tags=['登出'])
async def logout():
    pass

@public_router.get(path='/refresh',tags=['令牌刷新'])
async def refresh():
    pass
