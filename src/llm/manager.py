"""
统一 LLM 管理器

支持: MiniMax, ModelScope, DeepSeek
配置来源: config.yaml

功能:
- 单次推理 (complete)
- 批量推理 (complete_batch)
- 流式生成 (stream)
"""
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator, Protocol, runtime_checkable

from src.config import load_config

log = logging.getLogger(__name__)


# ============ Protocol ============

@runtime_checkable
class LLMProviderProtocol(Protocol):
    """LLM Provider 协议"""

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """单次推理"""
        ...

    def complete_batch(
        self, system_prompt: str, user_prompts: list[str], json_mode: bool = False
    ) -> list[str]:
        """批量推理"""
        ...

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式生成"""
        ...


# ============ Base Provider ============

class BaseProvider:
    """Provider 基类 - 提供统一的 complete_batch 实现"""

    def complete_batch(
        self, system_prompt: str, user_prompts: list[str], json_mode: bool = False
    ) -> list[str]:
        """批量推理 - 统一实现"""
        log.info(f"[complete_batch] 开始批量推理 {len(user_prompts)} 条")

        def call(prompt: str) -> str:
            return self.complete(system_prompt, prompt, json_mode)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(call, user_prompts))

        success_count = sum(1 for r in results if r)
        log.info(f"[complete_batch] 完成 {success_count}/{len(user_prompts)} 成功")
        return results


# ============ DeepSeek ============

class DeepSeekProvider(BaseProvider):
    """DeepSeek LLM 提供者"""

    def __init__(self, api_key: str, model: str = "deepseek-chat") -> None:
        from openai import OpenAI

        if not api_key:
            raise ValueError("请在 .env 文件中配置 DEEPSEEK_API_KEY 或 config.yaml")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        self.model = model
        log.info(f"[DeepSeekProvider] 初始化完成, model={model}")

    def complete(
        self, system_prompt: str, user_prompt: str, json_mode: bool = False
    ) -> str:
        """完成推理"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict = {"model": self.model, "messages": messages}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式生成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        stream = self.client.chat.completions.create(model=self.model, messages=messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ============ MiniMax ============

class MiniMaxProvider(BaseProvider):
    """MiniMax LLM 提供者"""

    BASE_URL = "https://api.minimaxi.com/v1"

    def __init__(self, api_key: str, group_id: str | None = None, model: str = "abab6.5s-chat") -> None:
        if not api_key:
            raise ValueError("请在 .env 文件中配置 MINIMAX_API_KEY 或 config.yaml")
        self.api_key = api_key
        self.group_id = group_id
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        log.info(f"[MiniMaxProvider] 初始化完成, model={model}")

    def _url(self, endpoint: str) -> str:
        url = f"{self.BASE_URL}{endpoint}"
        if self.group_id:
            url += f"?GroupId={self.group_id}"
        return url

    def complete(
        self, system_prompt: str, user_prompt: str, json_mode: bool = False
    ) -> str:
        """完成推理"""
        import requests

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(self._url("/chat_completion_v2"), headers=self.headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"MiniMax API 错误: {resp.text}")

        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("响应为空")
        return content

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式生成 - MiniMax 暂不支持，返回空迭代器"""
        log.warning("[MiniMaxProvider] 流式生成暂不支持")
        return iter([])


# ============ ModelScope (Qwen) ============

class ModelScopeProvider(BaseProvider):
    """ModelScope (Qwen) LLM 提供者"""

    def __init__(self, api_key: str, model: str = "qwen-turbo") -> None:
        from openai import OpenAI

        if not api_key:
            raise ValueError("请在 .env 文件中配置 MODELSCOPE_API_KEY 或 config.yaml")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api-inference.modelscope.cn/v1",
        )
        self.model = model
        log.info(f"[ModelScopeProvider] 初始化完成, model={model}")

    def complete(
        self, system_prompt: str, user_prompt: str, json_mode: bool = False
    ) -> str:
        """完成推理"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict = {"model": self.model, "messages": messages}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式生成"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        stream = self.client.chat.completions.create(model=self.model, messages=messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ============ LLM Manager ============

class LLMManager:
    """统一 LLM 管理器

    支持从 config.yaml 加载配置:
    ```yaml
    llm:
      default: "minimax"
      providers:
        minimax:
          api_key: "${MINIMAX_API_KEY}"
          base_url: "https://api.minimaxi.com/v1"
          model: "abab6.5s-chat"
        deepseek:
          api_key: "${DEEPSEEK_API_KEY}"
          model: "deepseek-chat"
        modelscope:
          api_key: "${MODELSCOPE_API_KEY}"
          model: "qwen-turbo"
    ```

    Usage:
        from src.llm import LLMManager

        # 使用 config.yaml 配置
        llm = LLMManager("deepseek")

        # 单次推理
        result = llm.complete("你是一个助手", "你好")

        # 批量推理
        results = llm.complete_batch("你是一个助手", ["问题1", "问题2"])

        # 流式生成
        for chunk in llm.stream("你是一个助手", "你好"):
            print(chunk, end="", flush=True)
    """

    def __init__(self, engine: str = "deepseek", config_path: str | None = None) -> None:
        """初始化 LLM 管理器

        Args:
            engine: 使用的 provider 名称 (minimax/deepseek/modelscope)
            config_path: 配置文件路径
        """
        self.engine = engine
        self.provider = self._create_provider(engine, config_path)

    def _create_provider(
        self, engine: str, config_path: str | None = None
    ) -> LLMProviderProtocol:
        """创建指定 provider"""
        try:
            config = load_config(config_path)
            providers = config.llm.providers

            if engine == "minimax" and providers.minimax:
                return MiniMaxProvider(
                    api_key=providers.minimax.api_key,
                    model=providers.minimax.model,
                )
            if engine == "deepseek" and providers.deepseek:
                return DeepSeekProvider(
                    api_key=providers.deepseek.api_key,
                    model=providers.deepseek.model,
                )
            if engine == "modelscope" and providers.modelscope:
                return ModelScopeProvider(
                    api_key=providers.modelscope.api_key,
                    model=providers.modelscope.model,
                )
        except Exception as e:
            log.warning(f"[LLMManager] 加载配置失败: {e}，使用环境变量")

        # 回退到环境变量
        return self._create_from_env(engine)

    def _create_from_env(self, engine: str) -> LLMProviderProtocol:
        """从环境变量创建 provider"""
        import os

        if engine == "minimax":
            return MiniMaxProvider(
                api_key=os.getenv("MINIMAX_API_KEY", ""),
                group_id=os.getenv("MINIMAX_GROUP_ID"),
            )
        if engine == "deepseek":
            return DeepSeekProvider(api_key=os.getenv("DEEPSEEK_API_KEY", ""))
        if engine == "modelscope":
            return ModelScopeProvider(api_key=os.getenv("MODELSCOPE_API_KEY", ""))
        raise ValueError(f"Unknown engine: {engine}")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """单次推理"""
        return self.provider.complete(system_prompt, user_prompt, json_mode)

    def complete_batch(
        self,
        system_prompt: str,
        user_prompts: list[str],
        json_mode: bool = False,
    ) -> list[str]:
        """批量推理"""
        return self.provider.complete_batch(system_prompt, user_prompts, json_mode)

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """流式生成"""
        return self.provider.stream(system_prompt, user_prompt)
