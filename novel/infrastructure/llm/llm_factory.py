# novel/infrastructure/llm/factory.py
from typing import Optional, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel



class LLMFactory:
    """
    LLM工厂：生产模型实例
    """

    @staticmethod
    def create_model(
            model_name: str,
            *,
            api_key: str,
            base_url: str,
            temperature: float = 0.7,
            max_tokens: int = 2048,
            top_p: float = 0.95,
            frequency_penalty: float = 0,
            presence_penalty: float = 0
    ) -> BaseChatModel:
        
        return ChatOpenAI(
            model=model_name,
            api_key= api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        
