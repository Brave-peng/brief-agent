"""
ModelScope 图片生成工具
使用 Z-Image-Turbo 模型生成图片

特性:
- 指数退避重试机制
- 速率限制 (Rate Limiting)
- 并发控制
- 详细的错误处理
"""
import os
import time
import json
import logging
import threading
from functools import wraps
from typing import Optional
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import typer
from PIL import Image
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

# 配置
DEFAULT_API_KEY = None  # 从环境变量 MODELSCOPE_API_KEY 读取
BASE_URL = "https://api-inference.modelscope.cn/"
DEFAULT_MODEL = "Tongyi-MAI/Z-Image-Turbo"
DEFAULT_WORKERS = 3

# 速率限制: 每秒最大请求数
DEFAULT_RATE_LIMIT = 2  # 2 requests/second
DEFAULT_TIMEOUT = 120   # 请求超时 (秒)
DEFAULT_POLL_INTERVAL = 3  # 轮询间隔 (秒)
DEFAULT_MAX_POLL_TIME = 600  # 最大轮询时间 (秒, 10分钟)

app = typer.Typer(help="ModelScope 图片生成工具")
logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置"""
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """计算指数退避延迟"""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class RateLimiter:
    """速率限制器"""
    def __init__(self, max_rate: float = DEFAULT_RATE_LIMIT):
        self.max_rate = max_rate  # 每秒请求数
        self.min_interval = 1.0 / max_rate
        self.last_request_time = 0.0
        self.lock = threading.Lock()

    def acquire(self) -> float:
        """获取令牌，返回等待时间"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = max(0, self.min_interval - elapsed)
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_request_time = time.time()
            return wait_time


@dataclass
class ImageResult:
    """图片生成结果"""
    success: bool
    output_path: str
    task_id: Optional[str] = None
    error: Optional[str] = None
    elapsed_time: float = 0.0


def with_retry(config: Optional[RetryConfig] = None):
    """重试装饰器"""
    if config is None:
        config = RetryConfig()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retry in {delay:.1f}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {config.max_retries + 1} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator


# 全局速率限制器
rate_limiter = RateLimiter(DEFAULT_RATE_LIMIT)


def generate_image(
    prompt: str,
    output_path: str = "result_image.jpg",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
    rate_limiter_instance: Optional[RateLimiter] = None,
) -> bool:
    """
    调用 ModelScope API 生成单张图片

    Args:
        prompt: 图片提示词
        output_path: 输出文件路径
        api_key: API Key
        model: 模型 ID
        max_retries: 最大重试次数
        rate_limiter_instance: 速率限制器实例

    Returns:
        是否成功
    """
    api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未配置 MODELSCOPE_API_KEY 环境变量")
    limiter = rate_limiter_instance or rate_limiter

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start_time = time.time()
    logger.info(f"[开始] {prompt[:40]}...")

    # 速率限制
    limiter.acquire()

    # 提交生成任务 (带重试)
    task_id = None
    retry_config = RetryConfig(max_retries=max_retries)

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                f"{BASE_URL}v1/images/generations",
                headers={**headers, "X-ModelScope-Async-Mode": "true"},
                data=json.dumps({"model": model, "prompt": prompt}, ensure_ascii=False).encode("utf-8"),
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 429:
                # Rate limit, wait and retry
                wait_time = int(response.headers.get("Retry-After", 5))
                logger.warning(f"[限流] 等待 {wait_time} 秒...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            task_id = response.json()["task_id"]
            logger.info(f"[提交] 任务ID: {task_id}")
            break

        except Exception as e:
            if attempt < max_retries:
                delay = retry_config.get_delay(attempt)
                logger.warning(f"[重试] {attempt + 1}/{max_retries}: {e} (等待 {delay:.1f}s)")
                time.sleep(delay)
            else:
                logger.error(f"[失败] {output_path}: {e}")
                return False

    if not task_id:
        return False

    # 轮询结果
    elapsed = time.time() - start_time
    while elapsed < DEFAULT_MAX_POLL_TIME:
        try:
            result = requests.get(
                f"{BASE_URL}v1/tasks/{task_id}",
                headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
                timeout=DEFAULT_TIMEOUT,
            )
            result.raise_for_status()
            data = result.json()
            status = data.get("task_status")

            if status == "SUCCEED":
                img_url = data["output_images"][0]
                img_response = requests.get(img_url, timeout=DEFAULT_TIMEOUT)
                img_response.raise_for_status()

                image = Image.open(BytesIO(img_response.content))
                image.save(output_path)
                elapsed = time.time() - start_time
                logger.info(f"[完成] {output_path} ({elapsed:.1f}s)")
                return True

            if status == "FAILED":
                error_msg = data.get("message", "未知错误")
                logger.error(f"[失败] {output_path}: {error_msg}")
                return False

            # 继续轮询
            time.sleep(DEFAULT_POLL_INTERVAL)
            elapsed = time.time() - start_time

        except requests.exceptions.Timeout:
            logger.warning("[超时] 轮询超时，继续等待...")
            time.sleep(DEFAULT_POLL_INTERVAL)
            elapsed = time.time() - start_time
        except Exception as e:
            logger.error(f"[错误] {e}")
            time.sleep(DEFAULT_POLL_INTERVAL)
            elapsed = time.time() - start_time

    logger.error(f"[超时] {output_path} (超过 {DEFAULT_MAX_POLL_TIME}s)")
    return False


def generate_images_batch(
    tasks: list[tuple[str, str]],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_workers: int = DEFAULT_WORKERS,
    rate_limit: float = DEFAULT_RATE_LIMIT,
) -> dict[str, bool]:
    """
    并发生成多张图片

    Args:
        tasks: [(prompt, output_path), ...] 列表
        api_key: API Key
        model: 模型 ID
        max_workers: 最大并发数
        rate_limit: 速率限制 (请求/秒)

    Returns:
        {output_path: success} 字典
    """
    # 创建专用的速率限制器
    limiter = RateLimiter(rate_limit)

    results = {}

    logger.info(f"[批量] 开始生成 {len(tasks)} 张图片 (并发: {max_workers}, 速率: {rate_limit}/s)")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(
                generate_image,
                prompt,
                output_path,
                api_key,
                model,
                rate_limiter_instance=limiter
            ): output_path
            for prompt, output_path in tasks
        }

        completed = 0
        total = len(future_to_path)
        for future in as_completed(future_to_path):
            completed += 1
            output_path = future_to_path[future]
            try:
                results[output_path] = future.result()
            except Exception as e:
                logger.error(f"[异常] {output_path}: {e}")
                results[output_path] = False

            # 进度显示
            logger.info(f"[进度] {completed}/{total}")

    success_count = sum(1 for v in results.values() if v)
    logger.info(f"\n[结果] {success_count}/{len(tasks)} 成功")

    return results


@app.command()
def gen(
    prompt: str = typer.Argument(..., help="图片描述提示词"),
    output: str = typer.Option("result_image.jpg", "-o", "--output", help="输出文件路径"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model", help="模型 ID"),
    key: Optional[str] = typer.Option(None, "-k", "--key", help="API Key"),
    retries: int = typer.Option(3, "-r", "--retries", help="最大重试次数"),
):
    """生成图片"""
    success = generate_image(
        prompt=prompt,
        output_path=output,
        api_key=key,
        model=model,
        max_retries=retries,
    )
    if not success:
        raise typer.Exit(1)


@app.command()
def batch(
    prompts_file: str = typer.Argument(..., help="提示词文件路径 (每行: prompt|output_path)"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model", help="模型 ID"),
    key: Optional[str] = typer.Option(None, "-k", "--key", help="API Key"),
    workers: int = typer.Option(DEFAULT_WORKERS, "-w", "--workers", help="并发数"),
    rate: float = typer.Option(DEFAULT_RATE_LIMIT, "-R", "--rate", help="速率限制 (请求/秒)"),
):
    """批量生成图片"""
    tasks = []
    with open(prompts_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                prompt, output_path = line.split("|", 1)
                tasks.append((prompt.strip(), output_path.strip()))

    results = generate_images_batch(
        tasks=tasks,
        api_key=key,
        model=model,
        max_workers=workers,
        rate_limit=rate,
    )

    failed = [k for k, v in results.items() if not v]
    if failed:
        logger.error("\n失败的任务:")
        for path in failed:
            logger.error(f"  - {path}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
