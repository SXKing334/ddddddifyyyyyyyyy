# novel\infrastructure\db\models\user.py
from sqlalchemy import Column, String, Integer

from novel.infrastructure.db.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    username = Column(String(64), nullable=False, comment="登录账号")
    role = Column(String(32), nullable=False, default='user', comment="角色：admin/agent/operator/viewer")
    password = Column(String(255), nullable=False, comment="加密密码")