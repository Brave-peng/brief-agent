"""
百炼 CosyVoice 音频提供者
"""
import os
from pathlib import Path

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, VoiceEnrollmentService, AudioFormat

# 预置音色
PRESET_VOICES: dict[str, str] = {
    "longxiaochun": "龙小淳 - 温柔女声",
    "longlaotie": "龙老铁 - 东北老铁",
    "longshu": "龙叔 - 成熟男声",
    "longxiaoxia": "龙小夏 - 活泼女声",
    "longxiaobai": "龙小白 - 知性女声",
    "longxiaochen": "龙小晨 - 阳光男声",
    "loongstella": "Stella - 知性女声(英文)",
}


class DashScopeProvider:
    """百炼 CosyVoice 音频提供者"""

    def __init__(self) -> None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请在 .env 文件中配置 DASHSCOPE_API_KEY")
        dashscope.api_key = api_key

    def clone_voice(self, audio_path: str, prefix: str = "my_voice") -> str:
        """注册克隆音色"""
        voice_service = VoiceEnrollmentService()
        audio_url = f"file://{os.path.abspath(audio_path)}" if os.path.exists(audio_path) else audio_path
        voice_id = voice_service.create_voice(
            target_model="cosyvoice-clone-v1",
            prefix=prefix,
            url=audio_url,
        )
        return voice_id

    def generate(self, text: str, voice_id: str, output_path: str) -> None:
        """生成音频"""
        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v1",
            voice=voice_id,
            format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
        )
        audio = synthesizer.call(text=text)
        if not audio:
            raise RuntimeError("音频合成失败，未返回音频数据")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio)
