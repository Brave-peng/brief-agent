"""Agent implementations for report generation"""

from src.models.llm import LLMManager

# 全局 LLM 管理器实例
_llm_manager: LLMManager | None = None


def get_llm() -> LLMManager:
    """获取全局 LLM 管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager("deepseek")
    return _llm_manager
