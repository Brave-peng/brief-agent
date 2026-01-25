"""
音频生成模块 - 支持百炼 CosyVoice 和 MiniMax 两种引擎
"""
from .generator import AudioEngine, AudioGenerator

__all__ = ["AudioEngine", "AudioGenerator"]
