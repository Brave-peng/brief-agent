"""
ModelScope 图片生成工具
使用 Z-Image-Turbo 模型生成图片
"""
import os
import time
import json
import requests
from io import BytesIO
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import typer
from PIL import Image
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
DEFAULT_API_KEY = "ms-14ad41f3-92a9-45f1-91c4-8aa67f7e13ad"
BASE_URL = "https://api-inference.modelscope.cn/"
DEFAULT_MODEL = "Tongyi-MAI/Z-Image-Turbo"
DEFAULT_WORKERS = 3

app = typer.Typer(help="ModelScope 图片生成工具")


def generate_image(
    prompt: str,
    output_path: str = "result_image.jpg",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> bool:
    """调用 ModelScope API 生成单张图片"""
    api_key = api_key or os.getenv("MODELSCOPE_API_KEY", DEFAULT_API_KEY)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"提交任务: {prompt[:50]}...")

    # 提交生成任务 (带重试)
    task_id = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}v1/images/generations",
                headers={**headers, "X-ModelScope-Async-Mode": "true"},
                data=json.dumps({"model": model, "prompt": prompt}, ensure_ascii=False).encode(
                    "utf-8"
                ),
                timeout=60,
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            print(f"任务已提交, ID: {task_id}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"重试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(2)
            else:
                print(f"提交失败: {e}")
                return False
    
    if not task_id:
        return False

    # 轮询结果
    start_time = time.time()
    while True:
        try:
            result = requests.get(
                f"{BASE_URL}v1/tasks/{task_id}",
                headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
                timeout=60,
            )
            result.raise_for_status()
            data = result.json()
            status = data.get("task_status")

            if status == "SUCCEED":
                img_url = data["output_images"][0]
                img_response = requests.get(img_url, timeout=60)
                img_response.raise_for_status()

                image = Image.open(BytesIO(img_response.content))
                image.save(output_path)
                print(f"完成: {output_path}")
                return True

            if status == "FAILED":
                print(f"失败 [{output_path}]: {data.get('message', '未知错误')}")
                return False

            # 超时检查 (5分钟)
            if time.time() - start_time > 300:
                print(f"超时: {output_path}")
                return False

            time.sleep(3)
        except requests.exceptions.Timeout:
            print(f"轮询超时，重试中...")
            time.sleep(2)


def generate_images_batch(
    tasks: list[tuple[str, str]],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_workers: int = DEFAULT_WORKERS,
) -> dict[str, bool]:
    """
    并发生成多张图片
    
    Args:
        tasks: [(prompt, output_path), ...] 列表
        api_key: API Key
        model: 模型 ID
        max_workers: 并发数，默认 3
    
    Returns:
        {output_path: success} 字典
    """
    results = {}
    
    print(f"开始并发生成 {len(tasks)} 张图片 (并发数: {max_workers})")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(generate_image, prompt, output_path, api_key, model): output_path
            for prompt, output_path in tasks
        }
        
        for future in as_completed(future_to_path):
            output_path = future_to_path[future]
            try:
                results[output_path] = future.result()
            except Exception as e:
                print(f"异常 [{output_path}]: {e}")
                results[output_path] = False
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n完成: {success_count}/{len(tasks)} 成功")
    
    return results


@app.command()
def gen(
    prompt: str = typer.Argument(..., help="图片描述提示词"),
    output: str = typer.Option("result_image.jpg", "-o", "--output", help="输出文件路径"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model", help="模型 ID"),
    key: Optional[str] = typer.Option(None, "-k", "--key", help="API Key"),
):
    """生成图片"""
    generate_image(prompt, output_path=output, api_key=key, model=model)


if __name__ == "__main__":
    app()

