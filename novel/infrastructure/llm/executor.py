# novel/infrastructure/llm/executor.py
from typing import Optional, AsyncGenerator, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from novel.infrastructure.llm.llm_factory import LLMFactory


class QwenExecutor:
    """
    模型节点的执行器
    """
    def __init__(
            self,
            model_name: str,
            *,
            api_key: str,
            **runtime_kwargs
    ):
        self.model: BaseChatModel = LLMFactory.create_model(model_name, api_key=api_key, **runtime_kwargs)

    async def invoke_with_struct(
            self
    )->Dict[str, Any]:
        pass


    async def invoke(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            **model_params
    ) -> str:
        """
        解耦，以便后续操作，不直接调用BaseChatModel的invoke方法
        :param prompt:
        :param system_prompt:
        :param model_params:
        :return:
        """
        # 确定规格（支持参数覆盖）

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await self.model.ainvoke(messages)

        return response.content

    async def stream(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            **model_params
    ) -> AsyncGenerator[str, None]:
        """
        解耦，以便后续操作，不直接调用BaseChatModel的invoke方法
        """

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        async for chunk in self.model.astream(messages):
            if chunk.content:
                yield chunk.content