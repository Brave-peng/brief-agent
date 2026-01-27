"""Service modules for RSS, LLM, and RAG"""

# LLM 已迁移到 src.models.llm
# 保留向后兼容导入
from src.models.llm import LLMManager


def get_llm(engine: str = "deepseek") -> LLMManager:
    """获取 LLM 管理器实例（向后兼容函数）"""
    return LLMManager(engine)
