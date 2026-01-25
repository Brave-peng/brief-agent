"""
DeepSeek LLM 提供者
"""
import os

from openai import OpenAI


class DeepSeekProvider:
    """DeepSeek LLM 提供者"""

    def __init__(self) -> None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        model = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
        if not api_key:
            raise ValueError("请在 .env 文件中配置 DEEPSEEK_API_KEY")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        self.model = model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """完成推理"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

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
