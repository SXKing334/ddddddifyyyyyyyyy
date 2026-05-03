# novel/infrastructure/db/models/workflow.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from sqlalchemy.sql import expression

from novel.infrastructure.db.base import Base


class WorkFlow(Base):
    __tablename__ = "workflow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, comment="租户ID（必须）")
    name = Column(String(100), nullable=False, comment="工作流名称：工作流1、工作流2...")
    flow_json = Column(JSON, nullable=False, comment="画布完整数据：节点、连线、配置、状态、未建完的数据")
    status = Column(
        Integer,
        nullable=False,
        server_default=expression.text("0"),
        comment="0=草稿 1=已发布 2=停用"
    )
    created_by = Column(Integer, nullable=True, comment="创建人ID")
    created_at = Column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )