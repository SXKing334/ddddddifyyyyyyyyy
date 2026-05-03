# novel\shared\converters\user_converter.py

from novel.domain.entity.user import User
from novel.infrastructure.db.models.user import User as UserORM
from novel.shared.schemas.user import User as UserSchema


def to_orm(user_entity: User) -> UserORM | None:
    """
    Domain Entity -> ORM Model
    用于保存数据到数据库
    """
    if not user_entity:
        return None

    return UserORM(
        id=user_entity.id,
        username=user_entity.username,
        password=user_entity.password,
        tenant_id=user_entity.tenant_id,
        role=user_entity.role
    )

def to_entity(user_schema: UserSchema) -> User | None:
    """
    ORM Model -> Domain Entity
    用于从数据库读取数据后转为业务实体
    """
    if not user_schema:
        return None

    return User(
        id=user_schema.id,
        username=user_schema.username,
        password=user_schema.password,  # 对应数据库里的 password 字段
        tenant_id=user_schema.tenant_id,
        role=user_schema.role
    )

def to_schema(user: UserORM) -> UserSchema | None:
    """
    Domain Entity -> Pydantic Schema
    用于接口响应
    """
    if not user:
        return None

    return UserSchema(
        id=user.id,
        username=user.username,
        role=user.role,
        tenant_id=user.tenant_id,
    )