"""Agent implementations for report generation"""

from src.services.llm import LLMService

# 全局 LLM 服务实例
_llm_service: LLMService | None = None


def get_llm() -> LLMService:
    """获取全局 LLM 服务实例"""
    global _llm_service
    if _llm_service is None:
        from src.config import load_config

        config = load_config()
        _llm_service = LLMService(config.llm)
    return _llm_service
