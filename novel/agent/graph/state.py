# novel\agent\state.py


from typing import Dict, List, Any, Optional
from langgraph.graph import MessagesState

class GlobalState(MessagesState):
    # 系统
    tenant_id: str
    session_id: str
    user_id: Optional[str]

    # 用户输入
    user_query: str
    user_files: List[str]  # 解析后的结果

    # 节点中间结果
    intent: str | None
    rag_context: str | None
    tool_result: Dict[str, Any] | None
    llm_output: Optional[str]

    # 最后结果
    final_answer: Optional[str]

    # 流程控制
    next_node: Optional[str]
    error_msg: Optional[str]

    # 自定义变量
    variables: Dict[str, Any]