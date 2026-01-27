"""Brief Agent - 企业级多模态知识内生 Agent 平台"""

from .config import load_config
from .models.llm import LLMManager

__all__ = ["load_config", "LLMManager"]
