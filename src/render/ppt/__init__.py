"""
PPT 构建模块

支持多种构建方式：
- direct: 直接渲染（python-pptx）
- marp: JSON → Marp Markdown → PPT
"""
from .base import PPTBuilder, BuilderRegistry
from .builder import DirectPPBuilder
from .marp_builder import MarpPPBuilder
from .json_to_marp import json_to_marp_markdown

__all__ = [
    "PPTBuilder",
    "BuilderRegistry",
    "DirectPPBuilder",
    "MarpPPBuilder",
    "json_to_marp_markdown",
]
