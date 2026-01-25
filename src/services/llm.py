"""
LLM 服务模块 - 支持多个 Provider

学习要点：
1. 同步 vs 异步调用
2. 流式输出 (streaming) - 逐步返回结果
3. Provider 抽象 - 统一接口切换后端
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Iterator

import httpx
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.config import LLMConfigWrapper


class LLMClient(ABC):
    """LLM 客户端基类"""

    @abstractmethod
    def generate(self, messages: List[dict], **kwargs) -> str:
        """同步生成"""
        pass

    @abstractmethod
    def stream(self, messages: List[dict], **kwargs) -> Iterator[str]:
        """流式生成 - 逐步返回结果"""
        pass


def _build_messages(messages: List[dict]):
    """将 dict 消息转换为 LangChain 消息"""
    from langchain_core.messages import HumanMessage, SystemMessage

    langchain_messages = []
    for msg in messages:
        if msg["role"] == "system":
            langchain_messages.append(SystemMessage(content=msg["content"]))
        else:
            langchain_messages.append(HumanMessage(content=msg["content"]))
    return langchain_messages


class OpenAICompatClient(LLMClient):
    """OpenAI 兼容接口的 LLM 客户端"""

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.7):
        self.client = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
        )

    def generate(self, messages: List[dict], **kwargs) -> str:
        """同步生成"""
        langchain_messages = _build_messages(messages)
        response = self.client.invoke(langchain_messages)
        return response.content

    def stream(self, messages: List[dict], **kwargs) -> Iterator[str]:
        """
        流式生成

        学习要点：
        - 使用 .stream() 方法获取异步迭代器
        - 每次迭代返回一个 chunk（片段）
        - 可以实时显示"打字机"效果
        """
        langchain_messages = _build_messages(messages)

        for chunk in self.client.stream(langchain_messages):
            if chunk.content:
                yield chunk.content


class LLMService:
    """LLM 服务管理器"""

    def __init__(self, config: LLMConfigWrapper):
        self.config = config
        self.clients = {}

        # 初始化各 provider
        if config.providers.minimax:
            self.clients["minimax"] = OpenAICompatClient(
                api_key=config.providers.minimax.api_key,
                base_url=config.providers.minimax.base_url or "https://api.minimaxi.com/v1",
                model=config.providers.minimax.model or "MiniMax-M2.1",
            )

        if config.providers.modelscope:
            self.clients["modelscope"] = OpenAICompatClient(
                api_key=config.providers.modelscope.api_key,
                base_url=config.providers.modelscope.base_url,
                model=config.providers.modelscope.model,
            )

        if config.providers.deepseek:
            self.clients["deepseek"] = OpenAICompatClient(
                api_key=config.providers.deepseek.api_key,
                base_url=config.providers.deepseek.base_url,
                model=config.providers.deepseek.model,
            )

    def get_client(self, provider: Optional[str] = None) -> LLMClient:
        """获取指定 provider 的客户端"""
        provider = provider or self.config.default
        if provider not in self.clients:
            raise ValueError(f"Unknown provider: {provider}")
        return self.clients[provider]

    def generate(self, prompt: str, provider: Optional[str] = None) -> str:
        """生成内容"""
        client = self.get_client(provider)
        messages = [{"role": "user", "content": prompt}]
        return client.generate(messages)

    def generate_with_system(
        self, system_prompt: str, user_prompt: str, provider: Optional[str] = None
    ) -> str:
        """带 system prompt 的生成"""
        client = self.get_client(provider)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return client.generate(messages)

    def stream(
        self, prompt: str, provider: Optional[str] = None
    ) -> Iterator[str]:
        """流式生成内容"""
        client = self.get_client(provider)
        messages = [{"role": "user", "content": prompt}]
        return client.stream(messages)

    def stream_with_system(
        self, system_prompt: str, user_prompt: str, provider: Optional[str] = None
    ) -> Iterator[str]:
        """带 system prompt 的流式生成"""
        client = self.get_client(provider)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return client.stream(messages)
