"""
音频生成模块 - 支持百炼 CosyVoice 和 MiniMax 两种引擎

Usage:
    from src.models.audio import AudioEngine, AudioGenerator

    generator = AudioGenerator(AudioEngine.DASHSCOPE)
    generator.generate("hello", "voice_id", "output.wav")
"""
from .generator import AudioEngine, AudioGenerator

__all__ = ["AudioEngine", "AudioGenerator"]
