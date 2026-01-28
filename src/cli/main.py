"""Brief Agent CLI - AI 驱动的知识平台

命令:
    rss     - RSS 内容处理 (fetch, parse, report)
    image   - 图片生成
    ppt     - PPT 相关
"""
import typer

from src.cli.image import app as image_app
from src.cli.ppt import ppt_app
from src.cli.rss import app as rss_app

app = typer.Typer(
    help="Brief Agent - AI 驱动的知识平台",
    add_completion=False,
    no_args_is_help=True,
)


def main() -> None:
    """CLI 入口"""
    app.add_typer(rss_app, name="rss")
    app.add_typer(image_app, name="image")
    app.add_typer(ppt_app, name="ppt")
    app()


if __name__ == "__main__":
    main()
