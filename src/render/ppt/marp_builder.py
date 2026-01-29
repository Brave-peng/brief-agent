"""
Marp PPT 构建器

JSON → Marp Markdown → PPT
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from .base import PPTBuilder, BuilderRegistry
from .json_to_marp import json_to_marp_markdown

logger = logging.getLogger(__name__)


# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"


@BuilderRegistry.register("marp")
class MarpPPBuilder(PPTBuilder):
    """Marp PPT 构建器"""

    def __init__(
        self,
        data: dict[str, Any],
        provider: str = "deepseek",
        template: str = "default",
        marp_cli_path: str | None = None,
    ) -> None:
        self.data = data
        self.provider = provider
        self.template = template
        self.template_path = TEMPLATES_DIR / f"{template}.md"
        self.marp_cli_path = marp_cli_path or self._find_marp_cli()
        if self.marp_cli_path is None:
            logger.warning("Marp CLI 未安装，PPT 渲染功能不可用")

    def _find_marp_cli(self) -> str | None:
        """查找 marp CLI"""
        # 先尝试 npm 全局安装的 marp
        try:
            result = subprocess.run(["which", "marp"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass

        # 检查本地安装
        local_marp = Path.home() / ".npm-global" / "bin" / "marp"
        if local_marp.exists():
            return str(local_marp)

        return None

    def build(self, output_path: str) -> None:
        """构建 PPT"""
        # 1. JSON → Marp Markdown（注入模板样式）
        marp_content = json_to_marp_markdown(self.data, template=self.template)
        marp_path = Path(output_path).with_suffix(".md")
        marp_path.write_text(marp_content, encoding="utf-8")
        logger.info("Marp Markdown 已生成: %s", marp_path)

        # 2. Marp → PPT
        if not self.marp_cli_path:
            raise RuntimeError(
                "Marp CLI 未安装。请执行以下命令安装:\n"
                "  npm install -g @marp-team/marp-cli\n\n"
                "或使用 direct 构建器（无需 Marp CLI）:\n"
                "  --builder direct"
            )
        self._render_with_marp(marp_path, output_path)

    def _render_with_marp(self, marp_path: Path, output_path: str) -> None:
        """使用 marp CLI 渲染"""
        # 使用 --theme-set 直接指定模板文件
        cmd = [
            self.marp_cli_path,
            str(marp_path),
            "--output",
            output_path,
            "--ppt",
            "--theme-set",
            str(self.template_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("PPT 已生成: %s (模板: %s)", output_path, self.template)
            else:
                logger.error("Marp 渲染失败: %s", result.stderr)
        except FileNotFoundError:
            logger.error("Marp CLI 未找到: %s", self.marp_cli_path)
