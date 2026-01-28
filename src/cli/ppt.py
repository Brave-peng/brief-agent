"""PPT 生成命令"""
from datetime import date as date_type
from pathlib import Path

import typer

from src.cli.ppt_converter import convert_markdown_to_ppt_data
from src.config import load_config
from src.llm import LLMManager
from src.render.ppt import BuilderRegistry

ppt_app = typer.Typer(
    help="PPT 相关命令",
    add_completion=False,
)


def generate_ppt_from_content(markdown_content: str, date: str, builder_name: str) -> None:
    """从 Markdown 内容生成 PPT"""
    from src.cli.ppt_converter import _fallback_structure

    typer.echo("正在结构化 PPT 内容...")

    # 1. LLM 智能拆分
    config = load_config()
    llm = LLMManager(config.llm.default)

    ppt_data = convert_markdown_to_ppt_data(markdown_content, llm, title=f"技术日报 | {date}")

    # 2. 获取构建器
    builder_cls = BuilderRegistry.get(builder_name)
    builder = builder_cls(data=ppt_data)

    # 3. 生成输出路径
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"简报_{date}.pptx"

    # 4. 构建 PPT
    builder.build(str(output_path))
    typer.echo(f"PPT 已保存: {output_path}")


# 便捷命令：直接根据报告 ID 生成 PPT
@ppt_app.command("from-report")
def ppt_from_report(
    report_id: int = typer.Argument(..., help="报告 ID"),
    builder: str = typer.Option("direct", "--builder", "-b", help="PPT 构建器: direct, marp"),
) -> None:
    """根据报告 ID 生成 PPT"""
    from src.storage import get_db

    db = get_db()
    report = db.get_report_by_id(report_id)

    if not report:
        typer.echo(f"报告不存在: {report_id}")
        raise typer.Exit(1)

    generate_ppt_from_content(report.content, str(report.date), builder)


# 便捷命令：从 Markdown 文件生成 PPT
@ppt_app.command("from-file")
def ppt_from_file(
    input_file: str = typer.Argument(..., help="Markdown 文件路径"),
    builder: str = typer.Option("direct", "--builder", "-b", help="PPT 构建器: direct, marp"),
) -> None:
    """从 Markdown 文件生成 PPT"""
    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"文件不存在: {input_file}")
        raise typer.Exit(1)

    content = input_path.read_text(encoding="utf-8")
    today = date_type.today().isoformat()

    generate_ppt_from_content(content, today, builder)
