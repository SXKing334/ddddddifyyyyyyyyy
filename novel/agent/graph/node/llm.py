# novel/agent/graph/node/llm.py
import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from novel.agent.graph.state import GlobalState
from novel.agent.utils.redis_client import get_redis_client       # 异步 Redis 客户端
from novel.agent.utils.db import async_update_conversation        # 异步数据库更新

from novel.infrastructure.llm.llm_factory import LLMFactory
from novel.utils.tenant_key import get_tenant_llm_config


async def call_llm(state: GlobalState, config: dict) -> GlobalState:
    """
    LLM 大模型调用节点（低代码工作流专用）
    :param state: 全局状态
    :param config: 节点配置（来自 flow_json 的 config 字段 + 注入的 next_nodes/conditions）
    :return: 更新后的状态
    """
    # 1. 从 state 提取基础信息
    tenant_id = state.get('metadata').tenant_id
    user_id = state.get('metadata').user_id
    session_id = state.get("metadata").session_id
    user_query = state.get("data").user_query
    files = state.get("data").user_file_ids

    if not tenant_id:
        raise ValueError("tenant_id 缺失，无法调用 LLM")
    if not user_query and not files:
        raise ValueError("user_query 和 files 均为空，无法处理")

    # 2. 文件内容
    if files:
        pass

    # 3. 有无RAG检索结果
    if state.get("data").current_node == 'RAG':
        pass


    # 4. 从节点配置获取 LLM 参数
    model_name = config.get("model_name", "gpt-3.5-turbo")
    system_prompt = config.get("system_prompt", "你是一个智能助手")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2048)
    top_p = config.get("top_p", 0.95)

    # 是否从租户配置覆盖某些参数（如模型名称）
    # 可以设计：节点配置优先级 > 租户默认配置
    # 这里先假设节点配置已包含最终使用的参数

    # 3. 获取租户的 LLM 认证信息（API Key, Base URL）
    tenant_llm_config = get_tenant_llm_config(tenant_id)
    api_key = tenant_llm_config.get("api_key")
    base_url = tenant_llm_config.get("base_url")
    if not api_key:
        raise PermissionError(f"租户 {tenant_id} 未配置 LLM API Key")

    # 4. 构建 LLM 实例
    llm: ChatOpenAI = LLMFactory.create_model(
        model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )

    # 5. 获取历史消息（Redis + 数据库回填）
    redis_client = get_redis_client()
    history_key = f"chat_history:{tenant_id}:{session_id}"
    # 尝试从 Redis 获取最近 N 条消息（例如 30 条）
    history_messages = await redis_client.lrange(history_key, -30, -1)
    if not history_messages:
        # 如果 Redis 没有，从数据库加载最近 30 条，并回写 Redis
        # 这里假设有异步函数 load_history_from_db
        from novel.agent.utils.db import load_history_from_db
        history_messages = await load_history_from_db(tenant_id, session_id, limit=30)
        if history_messages:
            # 回填 Redis（按顺序 push）
            for msg in history_messages:
                await redis_client.rpush(history_key, json.dumps(msg))

    # 解析历史消息为 langchain 消息对象
    langchain_messages = []
    # 首先加入系统提示
    langchain_messages.append(SystemMessage(content=system_prompt))
    for raw in history_messages:
        # 假设存储格式为 {"role": "user"|"assistant", "content": "..."}
        msg = json.loads(raw) if isinstance(raw, str) else raw
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
    # 最后加入当前用户问题（如果 user_query 非空且不在历史最后一条中）
    # 避免重复添加（简单处理：直接追加）
    langchain_messages.append(HumanMessage(content=user_query))

    # ========== 6. 调用 LLM ==========
    response = await llm.ainvoke(langchain_messages)
    llm_output = response.content

    # ========== 7. 将当前对话保存到 Redis 和数据库 ==========
    # 保存用户消息
    user_msg = {"role": "user", "content": user_query, "timestamp": ...}
    assistant_msg = {"role": "assistant", "content": llm_output, "timestamp": ...}
    await redis_client.rpush(history_key, json.dumps(user_msg), json.dumps(assistant_msg))
    # 可选：设置过期时间（如 7 天）
    await redis_client.expire(history_key, 7 * 24 * 3600)

    # 异步持久化到数据库（不阻塞主流程）
    # 可以创建后台任务，或直接 await
    await async_update_conversation(tenant_id, session_id, user_msg, assistant_msg)

    # ========== 8. 写入全局状态 ==========
    # 关键字段：供后续节点或条件边路由使用
    state["llm_output"] = llm_output
    state["final_answer"] = llm_output   # 若这是最终输出节点
    # 可选：追加到 messages 列表（如果 state 中有 messages 字段）
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append({"role": "user", "content": user_query})
    state["messages"].append({"role": "assistant", "content": llm_output})

    # 如果有文件引用，可以在这里处理文件内容（如上传到向量库）
    # 这部分根据你的业务实现

    # 条件边可能依赖的字段（例如：判断是否产生错误，或意图分类）
    # 如果 LLM 输出为空或包含特定标记，可以设置 state["need_fallback"] = True
    if not llm_output or len(llm_output.strip()) == 0:
        state["llm_error"] = "Empty response"

    return state