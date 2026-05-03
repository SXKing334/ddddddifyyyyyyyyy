#novel\agent\graph\node\start.py


from novel.agent.graph.state import GlobalState


async def start_node(state: GlobalState) -> GlobalState:
    """
    工作流【开始节点】
    作用：初始化流程、打印日志、校验基础参数、标记流程启动
    """
    # 1. 基础校验（必须字段）
    if not state.get("tenant_id"):
        raise ValueError("开始节点执行失败：tenant_id 不能为空")

    if not state.get("session_id"):
        raise ValueError("开始节点执行失败：session_id 不能为空")

    if not state.get("user_query"):
        raise ValueError("开始节点执行失败：user_query 用户问题不能为空")

    # 2. 你可以在这里加日志（可选）
    print(f"[开始节点] 租户={state['tenant_id']} 会话={state['session_id']}")
    print(f"用户问题：{state['user_query']}")

    # 3. 返回状态（必须 return state）
    return state