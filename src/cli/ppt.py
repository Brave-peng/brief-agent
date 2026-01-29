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


# 便捷命令：从 Markdown 文件生成 PPT（使用 AI 智能规划）
@ppt_app.command("from-md")
def ppt_from_md(
    input_file: str = typer.Argument(..., help="Markdown 文件路径"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径（默认自动生成）"),
    builder: str = typer.Option("marp", "--builder", "-b", help="PPT 构建器: marp, direct"),
    template: str = typer.Option(
        "default", "--template", "-t", help="模板: default, minimal, corporate, gradient, dark"
    ),
    max_slides: int = typer.Option(15, "--max-slides", "-m", help="最大幻灯片数量"),
    style: str = typer.Option(
        "academic", "--style", "-s", help="风格: academic, business, casual, minimal"
    ),
    provider: str = typer.Option(
        "deepseek", "--provider", "-p", help="LLM 提供商: deepseek, minimax, modelscope"
    ),
) -> None:
    """从 Markdown 文件智能生成 PPT（AI 驱动）

    示例:
        uv run python -m src.cli ppt from-md my_doc.md
        uv run python -m src.cli ppt from-md my_doc.md -o output.pptx -t corporate
    """
    from src.agents import plan_ppt_from_markdown
    from src.render.ppt import MarpPPBuilder, BuilderRegistry

    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"❌ 文件不存在: {input_file}", err=True)
        raise typer.Exit(1)

    # 读取 Markdown
    typer.echo(f"📄 读取文件: {input_file}")
    markdown_content = input_path.read_text(encoding="utf-8")
    typer.echo(f"📝 文档长度: {len(markdown_content)} 字符")

    # 使用 AI 规划 PPT 结构
    typer.echo(f"🤖 使用 AI 规划 PPT 结构 (provider: {provider})...")
    try:
        ppt_structure = plan_ppt_from_markdown(
            markdown_content=markdown_content,
            provider=provider,
            options={
                "max_slides": max_slides,
                "style": style,
                "focus": "key_insights",
            },
        )
        slide_count = len(ppt_structure.get("slides", []))
        typer.echo(f"✅ PPT 结构规划完成: {slide_count} 页")
    except Exception as e:
        typer.echo(f"❌ AI 规划失败: {e}", err=True)
        typer.echo(
            "💡 提示: 请确保 .env 文件中配置了 API Key (DEEPSEEK_API_KEY / MINIMAX_API_KEY / MODELSCOPE_API_KEY)",
            err=True,
        )
        raise typer.Exit(1)

    # 确定输出路径
    if output:
        output_path = Path(output)
    else:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_presentation.pptx"

    # 使用 MarpPPBuilder 生成 PPT
    typer.echo(f"🎨 生成 PPT (builder: {builder}, template: {template})...")
    try:
        if builder == "marp":
            builder_instance = MarpPPBuilder(ppt_structure, template=template)
        else:
            # 使用直接构建器
            builder_cls = BuilderRegistry.get("direct")
            builder_instance = builder_cls(ppt_structure)

        builder_instance.build(str(output_path))
        typer.echo(f"✅ PPT 生成成功: {output_path}")
    except Exception as e:
        typer.echo(f"❌ PPT 生成失败: {e}", err=True)
        raise typer.Exit(1)


# 便捷命令：从 Markdown 文件生成 PPT（旧版兼容，仍保留但标记为弃用）
@ppt_app.command("from-file")
def ppt_from_file(
    input_file: str = typer.Argument(..., help="Markdown 文件路径"),
    builder: str = typer.Option("direct", "--builder", "-b", help="PPT 构建器: direct, marp"),
) -> None:
    """从 Markdown 文件生成 PPT（旧版，建议使用 from-md）"""
    typer.echo("⚠️  此命令已弃用，建议使用: ppt from-md")

    from datetime import date as date_type

    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"文件不存在: {input_file}")
        raise typer.Exit(1)

    content = input_path.read_text(encoding="utf-8")
    today = date_type.today().isoformat()

    generate_ppt_from_content(content, today, builder)
