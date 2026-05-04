from novel.agent.graph.state import GlobalState


async def call_tool(state: GlobalState, config: dict) -> GlobalState:
    # config 中确定工具类型
