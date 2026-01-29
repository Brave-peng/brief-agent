#!/usr/bin/env python3
"""
CLI 入口点 - 使 python -m src.cli 可以正常工作

Usage:
    uv run python -m src.cli ppt from-md my_doc.md
    uv run python -m src.cli --help
"""

from src.cli.main import app

if __name__ == "__main__":
    app()
