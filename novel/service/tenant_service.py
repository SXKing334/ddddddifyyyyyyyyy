# novel\service\tenant_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# 假设的模型和 Schema
from novel.infrastructure.db.models.tenant import Tenant as TenantORM
from novel.infrastructure.db.models.user import User as UserORM
from novel.shared.schemas.public import APIResponse, TenantCreateRequest
from novel.shared.schemas.tenant import Tenant as TenantSchema
from novel.shared.schemas.user import User as UserSchema
from novel.utils.orm_to_dict import orm_to_dict


# 假设你有密码加密工具



class TenantService:
    """
    租户服务层
    """

    # 这里可以注入 Repo，比如检查配额等，目前暂时不需要
    def __init__(self):
        pass

    async def register(
            self,
            db: AsyncSession,
            data: TenantCreateRequest  # 包含公司名、管理员账号、密码等
    ) -> APIResponse:

        try:
            # 1. 校验租户名是否存在
            stmt = select(TenantORM).where(TenantORM.name == data.name)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                return APIResponse.failure(message="公司名称已存在")

            # 2. 创建租户
            new_tenant = TenantORM(
                name=data.name,
                app_id=data.app_id,
                plan=data.plan,
                secret=data.secret,
                created_at=data.created_at,
                quota_max_chats=data.quota_max_chats,
                is_active=data.is_active,
            )
            db.add(new_tenant)
            await db.flush()

            # 4. 创建默认管理员账号
            admin_user = UserORM(
                tenant_id=new_tenant.id,
                username=data.username,
                role="admin",
                password=data.password,
            )
            db.add(admin_user)
            await db.flush()

            # 5. 刷新对象以获取数据库生成的默认字段
            await db.refresh(new_tenant)
            await db.refresh(admin_user)

            # 6. 模型转换
            tenant_schema = TenantSchema.model_validate(new_tenant)
            user_schema = UserSchema.model_validate(admin_user)

            return APIResponse.success(
                data={
                    "tenant": tenant_schema,
                    "user": user_schema,
                },
                message="租户注册成功"
            )

        except IntegrityError as e:
            await db.rollback()
            return APIResponse.failure(message="注册失败：数据完整性错误（可能是用户名重复）")
        except Exception as e:
            await db.rollback()
            # 记录日志
            return APIResponse.failure(message=f"系统错误：{str(e)}")