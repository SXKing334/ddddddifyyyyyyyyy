# novel/agent/state.py
from typing import Dict, List, Any, Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from datetime import datetime


class NodeExecutionRecord(BaseModel):
    """单个节点执行记录"""
    node_id: str
    node_type: str
    input: Any = None
    output: Any = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class WorkflowMetadata(BaseModel):
    """工作流元数据（不常变）"""
    tenant_id: str
    session_id: str
    user_id: str
    workflow_id: str
    workflow_name: str
    start_time: datetime
    execution_id: str    # 唯一执行ID


class WorkflowData(BaseModel):
    """工作流数据（可变内容）"""
    # 用户输入（轻量）
    user_query: str = ""
    user_file_ids: List[str] = Field(default_factory=list)      # 只存ID，不存内容

    # 节点间传递的核心数据（只存引用）
    current_node: str
    node_outputs: Dict[str, Any] = Field(default_factory=dict)  # 只存关键输出
    variables: Dict[str, Any] = Field(default_factory=dict)     # 临时变量

    # 最终结果
    final_answer: Optional[str] = None

    # 流程控制
    error_msg: Optional[str] = None
    status: str = "running"  # running, paused, completed, failed


class GlobalState(MessagesState):
    """
    全局状态 - 分层设计
    企业级实践：元数据 + 数据 + 执行记录 分离
    """
    # 1. 元数据（小，常访问）
    metadata: WorkflowMetadata

    # 2. 业务数据（中等，节点间传递）
    data: WorkflowData

    # 3. 执行记录（大，只用于调试/审计，可选）
    execution_history: List[NodeExecutionRecord] = Field(default_factory=list)