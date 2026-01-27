"""
图片生成模块 - ModelScope Z-Image-Turbo

Usage:
    from src.models.image import generate_image, generate_images_batch

    # 单张生成
    generate_image("prompt", "output.jpg")

    # 批量生成
    generate_images_batch([("prompt1", "out1.jpg"), ("prompt2", "out2.jpg")])

阿里云图片生成请使用:
    from src.models.image.aliyun import generate_image as generate_image_aliyun
"""
from .image_modelscope import (
    generate_image,
    generate_images_batch,
    ImageResult,
    RetryConfig,
    RateLimiter,
)

__all__ = [
    "generate_image",
    "generate_images_batch",
    "ImageResult",
    "RetryConfig",
    "RateLimiter",
]
