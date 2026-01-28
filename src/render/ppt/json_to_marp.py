"""
JSON → Marp Markdown 转换器

支持新格式:
{
  "title": "技术日报 | 2026-01-25",
  "slides": [
    {
      "id": 1,
      "title": "GPT-5发布",
      "layout": "stack",           // 布局类型: stack, side-by-side, image-first, cards
      "image": "url或路径",        // 图片（可选）
      "image_position": "right",   // 图片位置: left/right (仅 side-by-side)
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

# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"

# 支持的布局类型
LAYOUTS = {"stack", "side-by-side", "image-first", "cards"}


def _load_template_style(template: str) -> str:
    """加载模板样式"""
    template_path = TEMPLATES_DIR / f"{template}.md"
    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        # 提取 <style>...</style> 部分
        import re
        style_match = re.search(r"<style>(.*?)</style>", content, re.DOTALL)
        if style_match:
            return f"<style>\n{style_match.group(1).strip()}\n</style>"
    return ""


def _build_layout_class(layout: str, image_position: str | None = None) -> str:
    """构建布局 class 字符串"""
    if layout == "stack":
        return "stack"
    elif layout == "side-by-side":
        if image_position == "left":
            return "side-by-side image-left"
        elif image_position == "right":
            return "side-by-side image-right"
        return "side-by-side"
    elif layout == "image-first":
        return "image-first"
    elif layout == "cards":
        return "cards"
    return "stack"


def json_to_marp_markdown(data: dict[str, Any], template: str = "default") -> str:
    """将 JSON 数据转换为 Marp Markdown"""
    lines = []

    # 加载模板样式并注入
    template_style = _load_template_style(template)

    # 封面
    lines.append("---")
    lines.append("paginate: false")
    lines.append("class: lead")
    lines.append("---")
    lines.append("")

    # 注入模板样式
    if template_style:
        lines.append(template_style)
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
        layout = slide.get("layout", "stack")
        image = slide.get("image", "")
        image_position = slide.get("image_position", "right")
        key_points = slide.get("key_points", "")
        bullet_points = slide.get("bullet_points", [])
        speaker_notes = slide.get("speaker_notes", "")

        lines.append("---")
        lines.append("")

        # 构建 class 字符串（布局 + 交替主题）
        classes = []
        if layout and layout != "stack":
            classes.append(layout)
        if image_position and layout == "side-by-side":
            classes.append(f"image-{image_position}")
        if slide_id % 2 == 0:
            classes.append("dark")

        if classes:
            lines.append(f"<!-- _class: {' '.join(classes)} -->")
            lines.append("")

        # 根据布局类型生成内容
        has_image = bool(image)
        use_flex_layout = layout in ("side-by-side", "image-first", "cards")

        if use_flex_layout and has_image and layout != "cards":
            # 左右分栏或图片优先布局
            lines.append('<div class="content">')
            lines.append(f"## {title}")
            lines.append("")
            if key_points:
                lines.append(f"**{key_points}**")
                lines.append("")
            for point in bullet_points:
                lines.append(f"- {point}")
            lines.append('</div>')
            lines.append("")
            lines.append('<div class="visual">')
            lines.append(f"![img]({image})")
            lines.append('</div>')
        elif layout == "cards" and bullet_points:
            # 卡片布局 - 每个要点一个卡片
            lines.append(f"## {title}")
            lines.append("")
            for point in bullet_points:
                lines.append(f'<div class="card">\n\n- {point}\n\n</div>')
            if image:
                lines.append("")
                lines.append(f"![img]({image})")
        else:
            # 默认垂直堆砌布局
            lines.append(f"## {title}")
            lines.append("")
            if key_points:
                lines.append(f"**{key_points}**")
                lines.append("")
            for point in bullet_points:
                lines.append(f"- {point}")
            lines.append("")
            if image:
                lines.append(f"![img]({image})")

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
