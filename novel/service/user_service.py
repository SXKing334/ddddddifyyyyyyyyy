# novel\service\user_service.py
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novel.infrastructure.db.models.tenant import Tenant as TenantORM
from novel.infrastructure.db.models.user import User as UserORM
from novel.infrastructure.redis.repo.tentant_repo import TenantRedisRepository, get_tenant_redis_repo
from novel.infrastructure.redis.repo.user_repo import UserRedisRepository, get_user_redis_repo
from novel.shared.schemas.public import APIResponse, LoginRequest
from novel.shared.schemas.tenant import Tenant as TenantSchema
from novel.shared.schemas.user import User as UserSchema
from novel.utils.orm_to_dict import orm_to_dict
from novel.utils.token_util import JwtUtil


class UserService:
    """
    用户服务层
    """

    def __init__(
            self,
            user_repo: UserRedisRepository = Depends(get_user_redis_repo),
            tenant_repo: TenantRedisRepository = Depends(get_tenant_redis_repo)
    ):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo

    async def login(
            self,
            db: AsyncSession,
            data: LoginRequest
    ) -> APIResponse:

        # 1. 接收请求参数
        tenant = data.tenant
        username = data.username
        password = data.password

        # 2. 参数效验
        if not username or not password or not tenant:
            return APIResponse.failure(code=400, message="账号,密码或者公司没填")

        # 3. 查询租户信息
        stmt = select(TenantORM).where(TenantORM.name == tenant)
        result = await db.execute(stmt)
        tenant_orm = result.scalar_one_or_none()

        # 4. 检查租户
        if not tenant_orm:
            return APIResponse.failure(message="公司不存在或者未被注册")

        # 5. 查数据库
        stmt = select(UserORM).where(
            UserORM.tenant_id == tenant_orm.id,
            UserORM.password == password,
            UserORM.username == username
        )
        result = await db.execute(stmt)
        user_orm = result.scalar_one_or_none()

        # 6.检查用户
        if not user_orm:
            return APIResponse.failure(message="账号或者密码错误，或者公司不存在")

        # 7. 刷新双token
        access_token = JwtUtil.create_access_token({"sub": user_orm.username,"uid": user_orm.id, "tid": user_orm.tenant_id})
        refresh_token = JwtUtil.create_refresh_token({"sub": user_orm.username,"uid": user_orm.id,"tid": user_orm.tenant_id})

        # 8.模型转化 ORM -> dict
        user_dict: dict = orm_to_dict(user_orm)
        tenant_dict: dict = orm_to_dict(tenant_orm)

        # 9.refresh_token, user_orm, tenant_orm 存 Redis
        try:
            await self.user_repo.set_user_info(user_orm.id, user_dict)
            await self.user_repo.set_user_refresh_token(user_orm.id, refresh_token)
            await self.tenant_repo.set_tenant_info(tenant_orm.id, tenant_dict)
        except Exception as e:
            # 正确开发中应该是日志
            print(f"登录时缓存失败{e}")
            raise e

        # 10. 模型转换 ORM -> Pydantic
        user_schema = UserSchema.model_validate(user_orm)
        tenant_schema = TenantSchema.model_validate(tenant_orm)

        # 11. 返回响应
        return APIResponse.success(
            code=200,
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_info":user_schema,
                "tenant":tenant_schema
            }
        )
