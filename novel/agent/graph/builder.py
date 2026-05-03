# novel\agent\graph\builder.py
from langgraph.graph import StateGraph

from novel.agent.graph.node.registry import get_node_func
from novel.agent.graph.state import GlobalState


class DynamicGraphBuilder:
    """
    动态流程图构建器
    从 flow_json 自动构建 LangGraph
    【低代码平台核心】
    """
    def __init__(self, flow_json: dict):
        self.tenant_id = flow_json['tenant_id'],    # 租户id
        self.user_id = flow_json['user_id'],        # 本次运行工作流的user_id
        self.session_id = flow_json['session_id'],  # 本次运行工作流的session_id(以便回溯)
        self.files = flow_json['files'],            # 上传的文件url

        self.nodes = flow_json["nodes"]             # LLM, RAG, MCP, web connection, skills, start, end节点
        self.edges = flow_json["edges"]             # 普通直连边
        self.conditions = flow_json["conditions"]   # 条件节点


    def build(self):
        """
        自动构建图
        """
        # 1. 创建图（使用全局唯一状态）
        workflow = StateGraph(GlobalState)

        # 2. 添加所有节点
        for node in self.nodes:
            node_id = node["id"]
            node_type = node["type"]
            node_config = node.get("config", {})

            # 从注册器获取节点函数
            node_func = get_node_func(node_type)

            # 包装函数：传入节点配置（关键！）
            def wrapped_node(state, config=node_config):
                return node_func(state, config)

            # 添加节点
            workflow.add_node(node_id, wrapped_node)

        # 3. 设置入口节点（找到 type=start 的节点）
        start_node_id = next(n["id"] for n in self.nodes if n["type"] == "start")
        workflow.set_entry_point(start_node_id)

        # 4. 添加所有连线
        for edge in self.edges:
            source = edge["source"]
            target = edge["target"]
            workflow.add_edge(source, target)

        # 5. 编译
        return workflow.compile()