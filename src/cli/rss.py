"""RSS 内容处理模块

命令:
    fetch   - 抓取 RSS 订阅源
    parse   - 解析未处理的文章
    report  - 生成日报/周报
"""
from datetime import datetime
from typing import Optional

import typer

from src.agents.article_parser_langgraph import parse_batch
from src.agents.report_workflow import generate_daily_report
from src.cli.ppt import generate_ppt_from_content
from src.config import load_config
from src.services.rss import RSSFetcher
from src.storage import get_db
from src.storage.logger import setup_logger

app = typer.Typer(
    help="RSS 内容处理",
    add_completion=False,
)


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
        None, help="指定要抓取的订阅源（默认：所有）"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
) -> None:
    """抓取 RSS 订阅源并将文章保存到数据库"""
    _setup_logging(verbose)
    config = load_config()
    db = get_db()

    fetcher = RSSFetcher(config.rss, db)

    count = fetcher.fetch_all()
    typer.echo(f"已抓取 {count} 篇文章")


@app.command("parse")
def parse_articles(
    limit: int = typer.Option(50, "--limit", "-l", help="最大解析文章数"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
) -> None:
    """使用 LLM 解析未处理的文章"""
    _setup_logging(verbose)
    db = get_db()

    unparsed = db.get_unparsed_articles()
    if not unparsed:
        typer.echo("没有未解析的文章")
        return

    article_ids = [a.id for a in unparsed[:limit]]
    results = parse_batch(article_ids)

    completed = sum(1 for r in results if r["status"] == "completed")
    failed = len(results) - completed

    typer.echo(f"解析完成: {completed}/{len(results)} 成功, {failed} 失败")


@app.command("report")
def generate_report(
    date: str = typer.Argument(..., help="日期，格式 YYYY-MM-DD"),
    output: bool = typer.Option(False, "--output", "-o", help="输出报告内容到终端"),
    ppt: bool = typer.Option(False, "--ppt", "-p", help="生成 PPT 文件"),
    builder: str = typer.Option("direct", "--builder", "-b", help="PPT 构建器: direct, marp"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
) -> None:
    """生成指定日期的日报"""
    _setup_logging(verbose)

    # 验证日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        typer.echo(f"无效的日期格式: {date}，请使用 YYYY-MM-DD")
        raise typer.Exit(1)

    result = generate_daily_report(date)

    if result["status"] == "completed":
        typer.echo(f"报告已生成: ID {result['report_id']}")
        if output:
            typer.echo("\n" + "=" * 60)
            typer.echo(result["report_content"])
            typer.echo("=" * 60)

        # 生成 PPT
        if ppt:
            typer.echo(f"正在使用 {builder} 构建器生成 PPT...")
            generate_ppt_from_content(result["report_content"], date, builder)
    else:
        typer.echo(f"报告生成失败: {result.get('error', '未知错误')}")
        raise typer.Exit(1)
