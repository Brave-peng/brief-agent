"""Service modules for RSS, LLM, and RAG"""
from src.services.llm import LLMService


def get_llm() -> LLMService:
    """Get LLM service singleton instance."""
    from src.config import load_config

    config = load_config()
    return LLMService(config.llm)
