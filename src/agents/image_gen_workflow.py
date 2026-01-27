"""
图片生成 Agent 工作流

根据简报内容生成配图（无文字）
"""
import logging
from typing import Optional
from pathlib import Path

from src.models.image import generate_image

log = logging.getLogger(__name__)


# 无文字提示词模板（中文）
NO_TEXT_PROMPTS = {
    "tech": "现代科技感抽象插画，数据流动可视化，蓝紫色渐变，赛博朋克风格，未来感设计，无文字，无标语，无字母，无数字",
    "business": "专业商务抽象风格，企业蓝色主题，几何图形极简设计，现代简约，无文字，无标语，无字母，无数字",
    "nature": "自然风景抽象插画，柔和绿蓝色调，有机流动形状，和平宁静氛围，无文字，无标语，无字母，无数字",
    "abstract": "抽象艺术表达，动态色彩，流畅线条，当代设计风格，无文字，无标语，无字母，无数字",
    "medical": "医学科学抽象插画，白色和青色清洁色调，分子结构，专业医疗主题，无文字，无标语，无字母，无数字",
    "ai": "人工智能概念抽象，神经网络可视化，发光节点和连接，未来科技感，无文字，无标语，无字母，无数字",
    "gradient": "优雅渐变背景，流畅色彩过渡，现代抽象设计，无文字，无标语，无字母，无数字",
}

# 简报主题到提示词的映射
TOPIC_TO_PROMPT = {
    "le cun": NO_TEXT_PROMPTS["tech"],
    "ami labs": NO_TEXT_PROMPTS["tech"],
    "世界模型": NO_TEXT_PROMPTS["ai"],
    "大模型": NO_TEXT_PROMPTS["ai"],
    "文心": NO_TEXT_PROMPTS["tech"],
    "百度": NO_TEXT_PROMPTS["business"],
    "百川智能": NO_TEXT_PROMPTS["medical"],
    "医疗": NO_TEXT_PROMPTS["medical"],
    "创业": NO_TEXT_PROMPTS["business"],
    "融资": NO_TEXT_PROMPTS["business"],
    "发布会": NO_TEXT_PROMPTS["tech"],
    "开源": NO_TEXT_PROMPTS["tech"],
    "研究": NO_TEXT_PROMPTS["abstract"],
    "论文": NO_TEXT_PROMPTS["abstract"],
    "awards": NO_TEXT_PROMPTS["gradient"],
    "荣誉": NO_TEXT_PROMPTS["gradient"],
    "默认": NO_TEXT_PROMPTS["gradient"],
}


def analyze_image_prompts(content: str, count: int = 3) -> list[str]:
    """
    分析简报内容，生成配图提示词

    Args:
        content: 简报/文章内容
        count: 需要生成的图片数量

    Returns:
        提示词列表
    """
    content_lower = content.lower()

    # 根据关键词匹配提示词
    matched_prompts = []
    for keyword, prompt in TOPIC_TO_PROMPT.items():
        if keyword in content_lower:
            matched_prompts.append(prompt)

    # 如果没有匹配，使用默认
    if not matched_prompts:
        matched_prompts = [NO_TEXT_PROMPTS["default"]]

    # 循环使用提示词，直到达到目标数量
    prompts = []
    for i in range(count):
        base_prompt = matched_prompts[i % len(matched_prompts)]
        # 添加变体避免重复
        variant = f"{base_prompt} variant {i + 1}"
        prompts.append(variant)

    return prompts


def generate_image_agent(
    content: str,
    output_dir: str = "output/images",
    count: int = 3,
    api_key: Optional[str] = None,
) -> dict:
    """
    图片生成 Agent 主函数

    Args:
        content: 简报/文章内容
        output_dir: 输出目录
        count: 生成图片数量
        api_key: ModelScope API Key

    Returns:
        {
            "success": True/False,
            "images": [{"path": "...", "url": "..."}],
            "count": 生成数量
        }
    """
    log.info(f"[image_gen] 开始生成 {count} 张配图")

    # 1. 分析内容，生成提示词
    prompts = analyze_image_prompts(content, count)
    log.info(f"[image_gen] 生成 {len(prompts)} 个提示词")

    # 2. 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 3. 生成图片
    results = []
    for i, prompt in enumerate(prompts):
        output_path = Path(output_dir) / f"image_{i + 1}.jpg"

        success = generate_image(
            prompt=prompt,
            output_path=str(output_path),
            api_key=api_key,
        )

        if success:
            results.append({
                "path": str(output_path),
                "prompt": prompt,
                "index": i + 1,
            })
            log.info(f"[image_gen] 图片 {i + 1} 生成成功: {output_path}")
        else:
            log.warning(f"[image_gen] 图片 {i + 1} 生成失败")

    return {
        "success": len(results) == count,
        "images": results,
        "count": len(results),
        "requested": count,
    }


def quick_generate(
    topic: str,
    style: str = "tech",
    output_path: str = "output/images/quick_image.jpg",
    api_key: Optional[str] = None,
) -> bool:
    """
    快速生成单张图片

    Args:
        topic: 图片主题
        style: 风格 (tech/business/medical/ai/abstract/nature/gradient)
        output_path: 输出路径
        api_key: API Key

    Returns:
        是否成功
    """
    # 获取基础提示词
    base_prompt = NO_TEXT_PROMPTS.get(style, NO_TEXT_PROMPTS["gradient"])

    # 组合提示词
    prompt = f"{topic}, {base_prompt}"

    log.info(f"[image_gen] 快速生成: {style} 风格")

    return generate_image(
        prompt=prompt,
        output_path=output_path,
        api_key=api_key,
    )


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("用法:")
        print("  python image_gen_workflow.py <内容文件> [数量]")
        print("  python image_gen_workflow.py --quick <主题> [风格]")
        sys.exit(1)

    if sys.argv[1] == "--quick":
        topic = sys.argv[2] if len(sys.argv) > 2 else "AI technology"
        style = sys.argv[3] if len(sys.argv) > 3 else "tech"
        quick_generate(topic, style)
    else:
        content_file = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3

        with open(content_file, encoding="utf-8") as f:
            content = f.read()

        result = generate_image_agent(content, count=count)
        print(f"\n结果: {result['count']}/{result['requested']} 成功")
