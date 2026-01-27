"""LLM 推理模块 - 支持 MiniMax, ModelScope, DeepSeek

已迁移到 src.models.llm，建议使用:
    from src.models.llm import LLMManager

保留向后兼容导入:
    from src.llm import LLMManager
"""

# 导入自 models.llm
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
