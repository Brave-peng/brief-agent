"""
MiniMax LLM 提供者
"""
import os

import requests


class MiniMaxProvider:
    """MiniMax LLM 提供者"""

    BASE_URL = "https://api.minimaxi.com/v1"

    def __init__(self) -> None:
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID")
        if not self.api_key:
            raise ValueError("请在 .env 文件中配置 MINIMAX_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, endpoint: str) -> str:
        url = f"{self.BASE_URL}{endpoint}"
        if self.group_id:
            url += f"?GroupId={self.group_id}"
        return url

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """完成推理"""
        payload = {
            "model": "abab6.5s-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(self._url("/chat_completion_v2"), headers=self.headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"MiniMax API 错误: {resp.text}")

        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("响应为空")
        return content

    def complete_batch(
        self,
        system_prompt: str,
        user_prompts: list[str],
        json_mode: bool = False,
    ) -> list[str]:
        """批量推理"""
        from concurrent.futures import ThreadPoolExecutor

        def call(prompt: str) -> str:
            return self.complete(system_prompt, prompt, json_mode)

        with ThreadPoolExecutor(max_workers=10) as executor:
            return list(executor.map(call, user_prompts))
