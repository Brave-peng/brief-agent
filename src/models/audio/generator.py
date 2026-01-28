"""
统一音频生成器
"""
from enum import Enum

from .dashscope import DashScopeProvider, PRESET_VOICES as DASHSCOPE_VOICES
from .minimax import MiniMaxProvider, PRESET_VOICES as MINIMAX_VOICES


class AudioEngine(Enum):
    DASHSCOPE = "dashscope"
    MINIMAX = "minimax"


class AudioGenerator:
    """统一音频生成器"""

    VOICES: dict[AudioEngine, dict[str, str]] = {
        AudioEngine.DASHSCOPE: DASHSCOPE_VOICES,
        AudioEngine.MINIMAX: MINIMAX_VOICES,
    }

    def __init__(self, engine: AudioEngine = AudioEngine.DASHSCOPE) -> None:
        self.engine = engine
        self.provider: DashScopeProvider | MiniMaxProvider = self._create_provider()

    def _create_provider(self) -> DashScopeProvider | MiniMaxProvider:
        if self.engine == AudioEngine.DASHSCOPE:
            return DashScopeProvider()
        return MiniMaxProvider()

    def clone_voice(self, audio_path: str, prefix: str = "my_voice") -> str:
        """注册克隆音色"""
        return self.provider.clone_voice(audio_path, prefix)

    def generate(self, text: str, voice_id: str, output_path: str) -> None:
        """生成音频"""
        self.provider.generate(text, voice_id, output_path)

    def list_voices(self) -> dict[str, str]:
        """列出可用音色"""
        return self.VOICES[self.engine]
