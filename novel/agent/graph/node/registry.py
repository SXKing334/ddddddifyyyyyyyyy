# novel\agent\node\registry.py

from .start import call_start
from .end import call_end
from .llm import call_llm
from .rag import call_rag
from .tool import call_tool
from .web import call_web
from .skill import call_skill
from .mcp import call_mcp

# 节点注册表（前端也可以用这个生成节点面板！）
NODE_REGISTRY = {
    "start": call_start,
    "end": call_end,
    "llm": call_llm,
    "rag": call_rag,
    "tool": call_tool,
    "web":call_web,
    "skill":call_skill,
    "mcp":call_mcp
}

# 获取节点函数
def get_node_func(node_type: str):
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"不支持的节点类型：{node_type}")
    return NODE_REGISTRY[node_type]