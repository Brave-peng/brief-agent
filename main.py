"""RSS Daily - AI Powered RSS Report Generator

CLI commands:
    rss fetch     - Fetch RSS feeds
    rss parse     - Parse unprocessed articles
    rss report    - Generate daily/weekly reports
"""
from datetime import datetime
from pathlib import Path

import typer
from typing import Optional

from src.config import load_config
from src.storage import get_db
from src.storage.logger import setup_logger
from src.services.rss import RSSFetcher
from src.services.llm import LLMService
from src.agents.article_parser_langgraph import parse_batch
from src.agents.report_workflow import generate_daily_report
from src.render.ppt import BuilderRegistry, DirectPPBuilder

app = typer.Typer(
    name="rss",
    help="RSS Daily - AI Powered RSS Report Generator",
    add_completion=False,
)

# PPT 结构化生成 Prompt
PPT_GENERATE_PROMPT = """你是一个 PPT 内容策划专家。请分析以下日报内容，将其拆分为 PPT 幻灯片。

## 要求
1. 每页幻灯片是一个独立的话题/新闻
2. 内容要精简，适合快速阅读
3. 只返回 JSON，不要有其他内容

## 输出 JSON 格式
{{"slides": [{{"id": 1, "title": "标题", "key_points": "一句话概括", "bullet_points": ["要点1", "要点2"], "speaker_notes": "完整的播报内容"}}]}}

## 规则
- title: 简洁标题，5-15 字
- key_points: 一句话关键信息，10-25 字
- bullet_points: 3-5 个精简要点，每条 5-15 字
- speaker_notes: 语音播报内容，30-80 字，可补充背景

## 识别规则
识别 markdown 中的每个 "## xxx" 或 "**xxx**" 格式的内容作为独立话题。

## 日报内容（直接提取内容，不要修改格式）
{markdown_content}

## 重要：只返回 JSON，用 {{}} 包裹，如 {{"slides": [...]}}"""


def _setup_logging(verbose: bool) -> None:
    """配置日志"""
    config = load_config()
    log_level = "DEBUG" if verbose else config.logging.level
    setup_logger(
        log_file=config.logging.file,
        level=log_level,
        rotation=config.logging.rotation,
        retention=config.logging.retention,
    )


@app.command("fetch")
def fetch_feeds(
    feed_name: Optional[str] = typer.Argument(
        None, help="Specific feed name to fetch (default: all feeds)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Fetch RSS feeds and save articles to database."""
    _setup_logging(verbose)
    config = load_config()
    db = get_db()

    fetcher = RSSFetcher(config.rss, db)

    count = fetcher.fetch_all()
    typer.echo(f"Fetched {count} articles")


@app.command("parse")
def parse_articles(
    limit: int = typer.Option(50, "--limit", "-l", help="Max articles to parse"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Parse unprocessed articles using LLM."""
    _setup_logging(verbose)
    db = get_db()

    unparsed = db.get_unparsed_articles()
    if not unparsed:
        typer.echo("No unparsed articles found")
        return

    article_ids = [a.id for a in unparsed[:limit]]
    results = parse_batch(article_ids)

    completed = sum(1 for r in results if r["status"] == "completed")
    failed = len(results) - completed

    typer.echo(f"Parsed: {completed}/{len(results)} successful, {failed} failed")


@app.command("report")
def generate_report(
    date: str = typer.Argument(..., help="Date in YYYY-MM-DD format"),
    output: bool = typer.Option(False, "--output", "-o", help="Print report to stdout"),
    ppt: bool = typer.Option(False, "--ppt", "-p", help="Generate PPT file"),
    builder: str = typer.Option("direct", "--builder", "-b", help="PPT builder: direct, marp"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Generate daily report for specified date."""
    _setup_logging(verbose)

    # 验证日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        typer.echo(f"Invalid date format: {date}. Use YYYY-MM-DD")
        raise typer.Exit(1)

    result = generate_daily_report(date)

    if result["status"] == "completed":
        typer.echo(f"Report generated: ID {result['report_id']}")
        if output:
            typer.echo("\n" + "=" * 60)
            typer.echo(result["report_content"])
            typer.echo("=" * 60)

        # 生成 PPT
        if ppt:
            typer.echo(f"Generating PPT with builder: {builder}")
            _generate_ppt(result["report_content"], date, builder)
    else:
        typer.echo(f"Report generation failed: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)


def _generate_ppt(markdown_content: str, date: str, builder_name: str) -> None:
    """生成 PPT"""
    typer.echo("正在结构化 PPT 内容...")

    # 1. LLM 智能拆分
    config = load_config()
    llm_service = LLMService(config.llm)

    prompt = PPT_GENERATE_PROMPT.format(markdown_content=markdown_content)
    json_str = llm_service.generate(prompt, provider=config.llm.default)

    # 解析 JSON
    import json
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        typer.echo("Warning: LLM 返回格式错误，使用降级方案")
        # 降级：提取标题后简单拆分
        data = _fallback_structure(markdown_content)

    slides = data.get("slides", [])

    # 2. 提取标题（第一页的标题或默认）
    title = f"技术日报 | {date}"
    if slides:
        # 从第一页获取或生成标题
        title = slides[0].get("title", title)

    # 3. 构建完整数据
    ppt_data = {
        "title": title,
        "slides": slides,
    }

    # 4. 获取构建器
    builder_cls = BuilderRegistry.get(builder_name)
    builder = builder_cls(data=ppt_data)

    # 5. 生成输出路径
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"简报_{date}.pptx"

    # 6. 构建 PPT
    builder.build(str(output_path))
    typer.echo(f"PPT saved: {output_path}")


def _fallback_structure(markdown_content: str) -> dict:
    """降级方案：简单的结构化"""
    lines = markdown_content.strip().split("\n")
    slides = []
    for i, line in enumerate(lines[1:], start=1):
        line = line.strip()
        if line and not line.startswith("#"):
            slides.append({
                "id": i,
                "title": f"话题 {i}",
                "key_points": line[:30] + "...",
                "bullet_points": [line[:50]],
                "speaker_notes": line,
            })
    return {"slides": slides}


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8000, "--port", help="Port to bind"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Start the RSS Daily web server (placeholder)."""
    typer.echo(f"Server starting on {host}:{port}")
    typer.echo("Web UI not implemented yet. Use CLI commands for now.")
    raise typer.Exit()


def main() -> None:
    """Entry point"""
    app()


if __name__ == "__main__":
    main()
