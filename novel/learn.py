import asyncio
import os
from hashlib import md5
from typing import Callable, Any, Dict, List, Required, NotRequired, Annotated, TypedDict

from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware, \
    ToolCallLimitMiddleware, ModelFallbackMiddleware, dynamic_prompt
from langchain.agents.structured_output import ToolStrategy

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, RemoveMessage
from langchain_core.prompts import  ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolRuntime
from langgraph.runtime import Runtime
from langgraph.types import Command, Checkpointer, Interrupt
from memory_ import MySQLMemorySaver, mysql_pool

load_dotenv()
class MyCallBack(BaseCallbackHandler):
    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs: Any
    ) -> Any:
        print(f"聊天记录：{messages}")

    # 修正：流式 Token 回调
    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        print(token, end="", flush=True)
def get_llm() -> BaseChatModel:
    API_KEY = os.getenv("QWEN_API_KEY","")
    modle = os.getenv("QWEN_MODEL","")
    BASE_URL = os.getenv("QWEN_BASE_URL","")
    return ChatOpenAI(
        api_key=API_KEY,
        model=modle,
        base_url=BASE_URL,
        callbacks=[MyCallBack()],
        streaming=True
    )
class MyState(AgentState):
    user_id : Required[Annotated[str, "用户id"]]
    thread_id : NotRequired[Annotated[str, "会话id"]]
class MyContext(TypedDict):
    agent: str
    user_id : str

config:RunnableConfig = {
    "configurable":{
        "thread_id": "123"
    }
}



@tool()
def get_weather(runtime: ToolRuntime[MyContext, MyState], position: str) -> str:
    """获取天气信息

    Args:
        position: 查询的地点
    """
    # 调用外部api
    weather = "晴转多云"
    t = "15℃"

    state = runtime.state
    config = runtime.config
    context = runtime.context
    #print(state)
    #print(config)
    #print(context)

    return position + " 天气："+weather+"，温度："+ t
@tool
def clear_conversation(runtime: ToolRuntime[MyContext, MyState]) -> Command:
    """清除会话

    """
    if not MyState["messages"]:
        return Command()
    return Command(
        update={
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
        }
    )

goal = ToolCallLimitMiddleware(thread_limit=20, run_limit=10)

async def get_agent(sql_pool) -> CompiledStateGraph:
    """创建一个agent"""
    model = get_llm()
    return create_agent(
        model=model,
        tools=[get_weather, clear_conversation],
        state_schema=MyState,
        context_schema=MyContext,
        checkpointer=MySQLMemorySaver(conn_pool=sql_pool),
        middleware=[
            # 总结中间件
            SummarizationMiddleware(
                max_tokens=1000,
                max_num_messages=10,
                exit_behavior="exit",
                exit_message="会话已结束"
            ),
            # 人在回路中间件
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "get_weather":{
                        "allowed_decisions":["approve", "edit", "reject"],
                        "description": "AI 要调用天气查询，请审批"
                    }
                }
            ),
            # 模型限制中间件
            ModelCallLimitMiddleware(
                thread_limit=10,
                run_limit= 5,
                exit_behavior="exit",                 # 超出限制退出
                exit_message="超过调用限制，请重新开始"   # 退出提示
            ),
            # 工具限制中间件
            ToolCallLimitMiddleware(
                thread_limit=10,
                run_limit= 5,
                exit_behavior="exit",                 # 超出限制退出
                exit_message="超过调用限制，请重新开始"   # 退出提示
            ),
            # 模型回退中间件
            ModelFallbackMiddleware(
                model_name="gpt-3.5-turbo-16k",
                exit_behavior="exit",
            ),

        ],
        response_format= ToolStrategy[StructuredResponseT] |
    )




async def main():
    sql_pool = await mysql_pool()
    try:
        agent = await get_agent(sql_pool)
        print("=" * 50)
        print("第一轮调用 → 触发工具 → 人工中断")
        print("=" * 50)
        res = await agent.ainvoke(
            input={
                "messages": [
                    ("system", "你是一个智能助手"),
                    ("user", "你好，帮我查一下旧金山的天气怎么样")
                ],
                "user_id": "3354647115",

            },
            config=config,
            context={
                "agent": "bb",
                "user_id": "3354647115"
            }
        )
        print("\n【中断返回】", res)

        # 2. 人工审批：同意执行
        print("\n" + "=" * 50)
        print("人工审批：同意调用天气工具")
        print("=" * 50)




        resume = Command(resume={
            "decisions": [{"type": "approve"}]
        })
        res = await agent.ainvoke(resume, config=config)
        print("\n【最终结果】", res)

    except Exception as e:
        res = e
        print(res)

    finally:
        sql_pool.close()
        await sql_pool.wait_closed()


if __name__ == '__main__':



    asyncio.run(main())
