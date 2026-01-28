"""Markdown 转 PPT 结构化数据"""
from pathlib import Path

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


def convert_markdown_to_ppt_data(
    markdown_content: str,
    llm,
    title: str | None = None,
) -> dict:
    """将 Markdown 内容转换为 PPT 结构化数据

    Args:
        markdown_content: Markdown 文本
        llm: LLM 实例
        title: 可选的标题

    Returns:
        PPT 结构化数据 {"title": str, "slides": [...]}
    """
    import json

    prompt = PPT_GENERATE_PROMPT.format(markdown_content=markdown_content)
    json_str = llm.complete("", prompt)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        data = _fallback_structure(markdown_content)

    slides = data.get("slides", [])

    # 使用提供的标题或从第一页提取
    result_title = title or (slides[0].get("title") if slides else "简报")

    return {
        "title": result_title,
        "slides": slides,
    }


def _fallback_structure(markdown_content: str) -> dict:
    """降级方案：简单的结构化"""
    lines = [
        l for l in markdown_content.strip().split("\n") if l.strip() and not l.startswith("#")
    ]
    slides = []
    for i, line in enumerate(lines, start=1):
        slides.append(
            {
                "id": i,
                "title": f"话题 {i}",
                "key_points": line[:30] + "...",
                "bullet_points": [line[:50]],
                "speaker_notes": line,
            }
        )
    return {"slides": slides}
