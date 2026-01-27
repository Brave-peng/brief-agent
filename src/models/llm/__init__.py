"""
LLM 推理模块 - 支持 MiniMax, ModelScope, DeepSeek

Usage:
    from src.models.llm import LLMManager

    llm = LLMManager("deepseek")
    result = llm.complete("system", "user")
"""
from .manager import (
    LLMManager,
    DeepSeekProvider,
    MiniMaxProvider,
    ModelScopeProvider,
    BaseProvider,
    LLMProviderProtocol,
)

__all__ = [
    "LLMManager",
    "DeepSeekProvider",
    "MiniMaxProvider",
    "ModelScopeProvider",
    "BaseProvider",
    "LLMProviderProtocol",
]
