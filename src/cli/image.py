"""图片生成模块

命令:
    gen     - 单张图片生成
    batch   - 批量图片生成
"""
from pathlib import Path

import typer

from src.config import load_config
from src.models.image import generate_image, generate_images_batch
from src.storage.logger import setup_logger

app = typer.Typer(
    help="图片生成",
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


@app.command("gen")
def image_gen(
    prompt: str = typer.Argument(..., help="图片生成提示词"),
    output: str = typer.Option("output/image.jpg", "--output", "-o", help="输出文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
) -> None:
    """使用 ModelScope Z-Image-Turbo 生成单张图片"""
    _setup_logging(verbose)
    typer.echo("正在生成图片...")
    result = generate_image(prompt, output)
    if result.success:
        typer.echo(f"图片已保存: {result.output_path} ({result.elapsed_time:.2f}秒)")
    else:
        typer.echo(f"失败: {result.error}")
        raise typer.Exit(1)


@app.command("batch")
def image_batch(
    input_file: str = typer.Argument(..., help="提示词文件（每行一个）"),
    output_dir: str = typer.Option("output/images", "--output", "-o", help="输出目录"),
    workers: int = typer.Option(3, "--workers", "-w", help="并发 worker 数"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="启用详细输出"),
) -> None:
    """从提示词文件批量生成图片"""
    _setup_logging(verbose)

    # 读取提示词文件
    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"文件不存在: {input_file}")
        raise typer.Exit(1)

    prompts = [line.strip() for line in input_path.read_text().split("\n") if line.strip()]
    if not prompts:
        typer.echo("没有找到提示词")
        return

    # 准备输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 批量生成
    tasks = [(prompt, str(output_path / f"img_{i:03d}.jpg")) for i, prompt in enumerate(prompts)]
    results = generate_images_batch(tasks, max_workers=workers)

    success = sum(1 for r in results.values() if r.success)
    failed = len(results) - success

    typer.echo(f"批量生成完成: {success}/{len(results)} 成功, {failed} 失败")
