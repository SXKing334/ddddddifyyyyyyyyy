# novel/agent/graph/builder.py
from langgraph.graph import StateGraph
from simpleeval import simple_eval

from novel.agent.graph.node.registry import get_node_func
from novel.agent.graph.state import GlobalState


# 全局需要剔除的 key（防止无限套娃）
EXCLUDE_KEYS = {"next_nodes", "conditions"}


class DynamicGraphBuilder:
    """
    动态流程图构建器
    从 flow_json 自动构建 LangGraph
    【低代码平台核心】
    """

    def __init__(self, flow_json: dict):
        self.tenant_id = flow_json['tenant_id']
        self.user_id = flow_json['user_id']
        self.session_id = flow_json['session_id']
        self.files = flow_json['files']

        self.nodes = flow_json["nodes"]                            # 普通节点的全部信息（不含条件节点）
        self.edges = flow_json["edges"]                            # 普通边
        self.conditions = flow_json.get("conditions", [])          # 条件节点（条件边）

        self.node_map = {node["id"]: node for node in self.nodes}  # 建立 id -> node 的索引
        self.downstream_map = {}                                   # 下游映射:{ source_id: [target_node,...]}
        self.condition_map = {}
        """
         条件映射:
         { 
           source_id:{
             default: target_node,
             branches:[
                {
                  condition: 条件1,
                  target_node: node信息,
                },
             ],
             config:condition_config
           },
          ...
        }
        """
        self._build_downstream_map()

    def _clean_node_config(self, config: dict) -> dict:
        """
        清理节点配置：
        剔除 next_nodes、conditions，防止无限套娃
        【你核心需求】
        """
        cleaned = {}
        for k, v in config.items():
            if k not in EXCLUDE_KEYS:
                cleaned[k] = v
        return cleaned

    def _build_downstream_map(self):
        """构建每个节点的下游节点配置映射（包括条件边）"""
        # 1. 处理普通直连边
        for edge in self.edges:
            source = edge["source"]
            target = edge["target"]

            # 初始化 source 为列表
            if source not in self.downstream_map:
                self.downstream_map[source] = []

            if isinstance(target, list):
                for item in target:
                    node = self.node_map.get(item)
                    if node:
                        self.downstream_map[source].append(node)

        # 2. 处理条件边
        for cond in self.conditions:
            default_node = self.node_map.get(cond["default"])  # 默认去的分支
            source = cond["source"]                            # 来这个节点的上一个节点id
            branches = cond.get("branches", {})                # 分支
            config = cond["config"]                            # 条件分支节点的配置类

            branch_list = []
            for condition_expr, target_id in branches.items():
                target_node = self.node_map.get(target_id)
                branch_list.append({
                    "condition": condition_expr,
                    "target_node": target_node     # 存入完整节点
                })

            # 存储条件分支信息
            self.condition_map[source] = {
                "default": default_node,
                "branches": branch_list,
                "config": config
            }

    async def build(self):
        """
        自动构建图
        """
        # 1. 创建图
        workflow = StateGraph(GlobalState)

        # 2. 添加所有节点
        for node in self.nodes:
            node_id = node["id"]
            node_type = node["type"]
            node_config = node.get("config", {})

            node_config['type'] = node_type
            node_config['node_id'] = node_id

            # 3. 直接边 注入下游节点配置
            if node_id in self.downstream_map:
                node_config['next_nodes'] = [
                    {
                        "id": n["id"],
                        "type": n["type"],
                        "config": self._clean_node_config(n.get("config", {}))                # 把下一个节点的配置里的 next_nodes 和 conditions 剔除，防止无限套娃
                    }
                    for n in self.downstream_map[node_id]
                ]

            # 4.条件边 注入分支和条件配置
            if node_id in self.condition_map:
                cond_info = self.condition_map[node_id]

                node_config["conditions"] = {
                    "default": cond_info["default"],
                    "branches": [
                        {
                            "condition": cond_info["condition"],
                            "target":{
                                "id": b["target_node"]['id'],
                                "type":b["target_node"]["type"],
                                "config":self._clean_node_config(b["target_node"]["config"])   # 把下一个节点的配置里的 next_nodes 和 conditions 剔除，防止无限套娃
                            }
                        } for b in cond_info["branches"]
                    ],
                    "config": node_config["config"]                       # 当前条件节点的配置
                }

            # 5. 获取节点函数
            node_func = get_node_func(node_type)

            # 6. 封装state和配置
            def wrapped_node(state, config=node_config):
                return node_func(state, config)

            workflow.add_node(node_id, wrapped_node)

        # 7. 设置入口节点
        start_node_id = next(n["id"] for n in self.nodes if n["type"] == "start" or n["type"] == "llm")
        workflow.set_entry_point(start_node_id)

        # 8. 添加普通连线
        for edge in self.edges:
            source = edge["source"]
            targets = edge["target"]
            if isinstance(targets, str):
                targets = [targets]
            for target in targets:
                workflow.add_edge(source, target)

        # 9. 添加条件边
        def evaluate_condition(expr: str, state: dict) -> bool:
            try:
                # 允许访问 state 字典，支持 state['intent'] 和 state.intent
                return simple_eval(expr, names={"state": state})
            except Exception:
                return False
        for source, cond_info in self.condition_map.items():
            default_node = cond_info["default"]  # 节点对象
            branches = cond_info["branches"]     # [{"condition":..., "target_node":...}]

            # 构建路由函数
            def make_router(branches, default_node):
                async def router(state: GlobalState):
                    # 将 state 转为字典供表达式求值
                    state_dict = state.model_dump() if hasattr(state, "model_dump") else dict(state)
                    for branch in branches:
                        expr = branch["condition"]
                        target_node = branch["target_node"]
                        if evaluate_condition(expr, state_dict):
                            return target_node["id"]
                    return default_node["id"]
                return router

            workflow.add_conditional_edges(source, make_router(branches, default_node))
        # 10. 编译
        return workflow.compile()