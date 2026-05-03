# novel/infrastructure/db/models/tenant.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from novel.infrastructure.db.base import Base


class Tenant(Base):
    __tablename__ = 'tenant'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键 ID（自增）")
    name = Column(String(100), nullable=False, comment="租户名称（公司名 / 品牌名）")
    app_id = Column(String(64), nullable=False, unique=True, index=True, comment="租户唯一标识")
    secret = Column(String(128), nullable=False, comment="密钥（密码）")
    plan = Column(String(32), nullable=False, comment="套餐版本 (free/basic/pro/enterprise)")
    quota_max_chats = Column(Integer, nullable=False, comment="最大对话次数配额")
    created_at = Column(DateTime, nullable=False, server_default=func.now(),comment="创建时间")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    qwen_api_key = Column(String(255),comment="qwen api key")