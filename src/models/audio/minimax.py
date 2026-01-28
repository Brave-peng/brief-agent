"""
MiniMax TTS 音频提供者
"""
import os
from pathlib import Path

import requests

BASE_URL = "https://api.minimaxi.com/v1"

# 预置音色
PRESET_VOICES: dict[str, str] = {
    "male-shaun": "Shaun - 磁性男声",
    "female-annie": "Annie - 知性女声",
    "male-buster": "Buster - 浑厚男声",
    "female-crystal": "Crystal - 清亮女声",
}


class MiniMaxProvider:
    """MiniMax TTS 音频提供者"""

    def __init__(self) -> None:
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID")
        if not self.api_key:
            raise ValueError("请在 .env 文件中配置 MINIMAX_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def clone_voice(self, audio_path: str, prefix: str = "my_voice") -> str:
        """注册克隆音色"""
        # 上传文件
        upload_url = f"{BASE_URL}/files/upload"
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f)}
            data = {"purpose": "voice_clone"}
            resp = requests.post(upload_url, headers=self.headers, data=data, files=files)

        if resp.status_code != 200:
            raise RuntimeError(f"文件上传失败: {resp.text}")

        file_id = resp.json().get("file", {}).get("file_id")
        if not file_id:
            raise RuntimeError("无法获取 file_id")

        # 注册音色
        voice_id = f"custom_{prefix}"
        url = f"{BASE_URL}/voice_clone"
        if self.group_id:
            url += f"?GroupId={self.group_id}"

        payload = {
            "voice_id": voice_id,
            "file_id": file_id,
            "voice_name": prefix,
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"音色注册失败: {resp.text}")

        return voice_id

    def generate(self, text: str, voice_id: str, output_path: str) -> None:
        """生成音频"""
        url = f"{BASE_URL}/t2a_v2"
        if self.group_id:
            url += f"?GroupId={self.group_id}"

        payload = {
            "model": "speech-01-turbo",
            "text": text,
            "voice_id": voice_id if voice_id in PRESET_VOICES else "male-shaun",
        }

        resp = requests.post(url, headers=self.headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"音频合成失败: {resp.text}")

        data = resp.json()
        audio_url = data.get("audio_url") or data.get("audio")
        if not audio_url:
            raise RuntimeError("响应中未包含音频数据")

        # 下载或保存音频
        if audio_url.startswith("http"):
            audio_resp = requests.get(audio_url)
            if audio_resp.status_code != 200:
                raise RuntimeError("音频下载失败")
            content = audio_resp.content
        else:
            import base64
            content = base64.b64decode(audio_url)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(content)
