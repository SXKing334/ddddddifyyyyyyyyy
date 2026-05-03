# novel\agent\graph\node\llm
from novel.core.graph_state import GlobalState
from novel.infrastructure.llm.manager import LLMManager




# 大模型调用节点
async def call_llm(state: GlobalState, config: dict) -> GlobalState:
    """
    LLM 大模型调用节点（低代码工作流专用）
    :param state: 全局状态
    :param config: 节点配置（来自 flow_json）
    :return: 更新后的状态
    """
    # ==============================================
    # 1. 从全局状态拿必要信息
    # ==============================================
    tenant_id = state["tenant_id"]
    user_query = state["user_query"]
    messages = state.get("messages", [])

    # ==============================================
    # 2. 从节点配置（画布）拿用户设置的参数
    # ==============================================
    provider = config.get("provider", "openai")
    model_name = config.get("model_name", "gpt-3.5-turbo")
    system_prompt = config.get("system_prompt", "你是一个智能助手")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2048)
    top_p = config.get("top_p", 0.95)

    # ==============================================
    # 3. 从租户配置中获取 API Key / URL
    # 注意：这里 tenant 是从 DB 查询出来的租户信息
    # ==============================================
    tenant = state.get("tenant")  # 在执行前注入
    if not tenant:
        raise Exception("租户信息不存在，无法调用LLM")

    # ==============================================
    # 4. 通过工厂 + 缓存获取模型实例
    # ==============================================
    llm = LLMManager.get_llm(
        tenant_id=tenant_id,
        provider=provider,
        model_name=model_name,
        api_key=tenant["llm_api_key"],
        base_url=tenant["llm_api_url"],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p
    )

    # ==============================================
    # 5. 构建消息并调用模型
    # ==============================================
    messages = [
        ("system", system_prompt),
        ("human", user_query)
    ]

    response = await llm.ainvoke(messages)

    # ==============================================
    # 6. 结果写入全局状态
    # ==============================================
    state["llm_output"] = response.content
    state["final_answer"] = response.content  # 直接作为最终答案

    return state