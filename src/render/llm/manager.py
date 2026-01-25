"""
统一 LLM 管理器
"""
from enum import Enum

from .deepseek import DeepSeekProvider
from .minimax import MiniMaxProvider


class LLMEngine(Enum):
    DEEPSEEK = "deepseek"
    MINIMAX = "minimax"


class LLMManager:
    """统一 LLM 管理器"""

    def __init__(self, engine: LLMEngine = LLMEngine.DEEPSEEK) -> None:
        self.engine = engine
        self.provider: DeepSeekProvider | MiniMaxProvider = self._create_provider()

    def _create_provider(self) -> DeepSeekProvider | MiniMaxProvider:
        if self.engine == LLMEngine.DEEPSEEK:
            return DeepSeekProvider()
        return MiniMaxProvider()

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
