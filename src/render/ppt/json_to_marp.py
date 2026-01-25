"""
JSON → Marp Markdown 转换器

支持新格式:
{
  "title": "技术日报 | 2026-01-25",
  "slides": [
    {
      "id": 1,
      "title": "GPT-5发布",
      "key_points": "一句话关键信息",
      "bullet_points": ["要点1", "要点2"],
      "speaker_notes": "语音播报内容"
    }
  ]
}
"""
import json
from pathlib import Path
from typing import Any


def json_to_marp_markdown(data: dict[str, Any]) -> str:
    """将 JSON 数据转换为 Marp Markdown"""
    lines = []

    # 封面
    lines.append("---")
    lines.append("theme: default")
    lines.append("paginate: false")
    lines.append("class: lead")
    lines.append("---")
    lines.append("")
    lines.append("<!-- _class: cover -->")
    lines.append(f"# {data.get('title', '日报')}")
    lines.append("")

    # 封面页的 speaker_notes（如果有的话，取第一页的）
    slides = data.get("slides", [])
    if slides and len(slides) > 0:
        first_notes = slides[0].get("speaker_notes", "")
        if first_notes:
            lines.append(f"<!-- note: {first_notes} -->")
    lines.append("")

    # 内容页
    for i, slide in enumerate(slides):
        slide_id = slide.get("id", i + 1)
        title = slide.get("title", f"话题 {slide_id}")
        key_points = slide.get("key_points", "")
        bullet_points = slide.get("bullet_points", [])
        speaker_notes = slide.get("speaker_notes", "")

        lines.append("---")
        lines.append("")

        # 交替主题色
        if slide_id % 2 == 0:
            lines.append("<!-- _class: dark -->")
            lines.append("")

        # 标题
        lines.append(f"## {title}")
        lines.append("")

        # 关键点（作为引言）
        if key_points:
            lines.append(f"**{key_points}**")
            lines.append("")

        # 要点列表
        for point in bullet_points:
            lines.append(f"- {point}")
        lines.append("")

        # 语音备注
        if speaker_notes:
            lines.append(f"<!-- note: {speaker_notes} -->")
        lines.append("")

    # 结束页
    lines.append("---")
    lines.append("<!-- _class: ending -->")
    lines.append("# 谢谢观看")
    lines.append("")

    return "\n".join(lines)


def parse_json_content(content: str) -> dict[str, Any]:
    """解析 JSON 内容，尝试提取 JSON 对象"""
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown 代码块中提取
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取 {...} 模式
    brace_match = re.search(r'\{[\s\S]*\}', content)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("无法解析 JSON 内容")
