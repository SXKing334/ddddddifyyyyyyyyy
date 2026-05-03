# novel\agent\node\registry.py

from .start import start_node
from .end import end_node
from .llm import llm_node
from .rag import rag_node
from .tool import tool_node
from .condition import condition_node

# 节点注册表（前端也可以用这个生成节点面板！）
NODE_REGISTRY = {
    "start": start_node,
    "end": end_node,
    "llm": llm_node,
    "rag": rag_node,
    "tool": tool_node,
    "condition": condition_node,
}

# 获取节点函数
def get_node_func(node_type: str):
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"不支持的节点类型：{node_type}")
    return NODE_REGISTRY[node_type]