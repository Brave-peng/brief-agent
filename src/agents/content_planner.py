"""
ContentPlanner - 将任意 Markdown 文档转换为 PPT 结构

核心功能：
1. 分析 Markdown 内容结构和关键信息
2. 规划 PPT 页数、每页布局、配图建议
3. 输出符合 MarpPPBuilder 的结构化 JSON

特点：
- 支持 LLM 增强分析（需要配置 API Key）
- 没有 API Key 时也能使用基础规则解析
- 自动降级，优雅处理

Usage:
    from src.agents.content_planner import ContentPlanner

    planner = ContentPlanner()  # 自动检测是否有 LLM 可用
    ppt_structure = planner.plan(md_content, options={
        "max_slides": 12,
        "style": "academic",
        "focus": "key_insights"
    })

    # ppt_structure 可以直接传给 MarpPPBuilder
    builder = MarpPPBuilder(ppt_structure, template="academic")
    builder.build("output.pptx")
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContentPlanner:
    """内容规划器 - 将 Markdown 转换为 PPT 结构"""

    def __init__(self, provider: str = "deepseek") -> None:
        self.provider = provider
        self._llm = self._init_llm()

    def _init_llm(self):
        """初始化 LLM，失败则抛出异常"""
        try:
            from src.llm import LLMManager

            llm = LLMManager(self.provider)
            logger.info(f"[ContentPlanner] LLM 已初始化 (provider: {self.provider})")
            return llm
        except Exception as e:
            logger.error(f"[ContentPlanner] LLM 初始化失败: {e}")
            raise RuntimeError(
                "LLM 初始化失败。请检查:\n"
                "1. .env 文件中是否配置了 API Key (DEEPSEEK_API_KEY / MINIMAX_API_KEY / MODELSCOPE_API_KEY)\n"
                "2. config.yaml 中的 LLM 配置是否正确\n"
                "3. 网络连接是否正常"
            ) from e

    def plan(
        self,
        markdown_content: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        将 Markdown 内容规划为 PPT 结构

        Args:
            markdown_content: Markdown 格式的文档内容
            options: 可选配置
                - max_slides: 最大页数（默认自动决定）
                - style: 风格 (academic/business/casual/minimal)
                - focus: 重点 (key_insights/full_content/summary_only)

        Returns:
            符合 MarpPPBuilder 的 JSON 结构
        """
        options = options or {}

        logger.info(f"[ContentPlanner] 开始规划 PPT 结构，文档长度: {len(markdown_content)} 字符")

        try:
            # 使用 LLM 进行智能规划
            result = self._plan_with_llm(markdown_content, options)
            logger.info(f"[ContentPlanner] LLM 规划完成: {len(result.get('slides', []))} 页")
            return result

        except Exception as e:
            logger.error(f"[ContentPlanner] 规划失败: {e}")
            raise RuntimeError(f"PPT 结构规划失败: {e}") from e

    def _plan_with_llm(self, markdown_content: str, options: dict[str, Any]) -> dict[str, Any]:
        """使用 LLM 智能规划 PPT 结构"""
        system_prompt = """你是一位专业的内容设计师和 PPT 策划专家。

请将用户提供的 Markdown 文档转换为结构化的 PPT 大纲。

输出必须是 JSON 格式，符合以下结构：
{
  "title": "PPT主标题",
  "slides": [
    {
      "id": 1,
      "title": "页面标题",
      "layout": "布局类型(stack/side-by-side/image-first/cards)",
      "key_points": "一句话核心信息",
      "bullet_points": ["要点1", "要点2", "要点3"],
      "speaker_notes": "演讲者备注"
    }
  ]
}

注意：
- 第一页通常是封面页
- bullet_points 要简洁
- 整个 PPT 逻辑连贯"""

        user_prompt = f"""请将以下 Markdown 文档转换为 PPT 结构。

配置：
- 最大页数: {options.get("max_slides", 15)}
- 风格: {options.get("style", "academic")}

原始文档内容：

{markdown_content[:8000]}

请生成 JSON 格式的 PPT 结构。"""

        response = self._llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        return json.loads(response.strip())

    def _plan_with_rules(self, markdown_content: str, max_slides: int) -> dict[str, Any]:
        """使用基础规则解析 Markdown 为 PPT 结构"""
        lines = markdown_content.split("\n")

        # 提取主标题
        title = "演示文稿"
        for line in lines[:10]:
            if line.startswith("# ") and not line.startswith("## "):
                title = line.replace("# ", "").strip()
                break

        # 提取二级标题作为分页点
        sections = []
        current_section = {"title": "引言", "content": []}

        for line in lines:
            if line.startswith("## "):
                # 保存当前章节
                if current_section["content"]:
                    sections.append(current_section)
                # 开始新章节
                current_section = {"title": line.replace("## ", "").strip(), "content": []}
            elif line.startswith("- ") or line.startswith("* "):
                # 列表项
                current_section["content"].append(line[2:].strip())
            elif line.strip() and not line.startswith("#"):
                # 普通文本
                current_section["content"].append(line.strip())

        # 保存最后一章
        if current_section["content"]:
            sections.append(current_section)

        # 构建 PPT 结构
        slides = []

        # 封面页
        slides.append(
            {
                "id": 1,
                "title": title,
                "layout": "stack",
                "key_points": "",
                "bullet_points": [],
                "speaker_notes": "欢迎观看本次演示",
            }
        )

        # 内容页
        for i, section in enumerate(sections[: max_slides - 2], start=2):
            # 提取关键要点（最多5个）
            key_points = (
                section["content"][:5] if len(section["content"]) > 5 else section["content"]
            )

            # 确定布局
            if i % 3 == 0:
                layout = "side-by-side"
            elif i % 3 == 1:
                layout = "image-first"
            else:
                layout = "stack"

            slides.append(
                {
                    "id": i,
                    "title": section["title"],
                    "layout": layout,
                    "key_points": key_points[0] if key_points else "",
                    "bullet_points": key_points[1:] if len(key_points) > 1 else [],
                    "speaker_notes": f"本页主题: {section['title']}",
                }
            )

        # 结束页
        slides.append(
            {
                "id": len(slides) + 1,
                "title": "谢谢观看",
                "layout": "stack",
                "key_points": "",
                "bullet_points": [],
                "speaker_notes": "感谢聆听，欢迎提问",
            }
        )

        return {"title": title, "slides": slides}

    def _create_fallback_structure(self, markdown_content: str) -> dict[str, Any]:
        """创建最基础的回退结构（当所有方法都失败时使用）"""
        lines = markdown_content.split("\n")

        # 尝试提取标题
        title = "演示文稿"
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        return {
            "title": title,
            "slides": [
                {
                    "id": 1,
                    "title": title,
                    "layout": "stack",
                    "key_points": "",
                    "bullet_points": ["文档内容已加载"],
                    "speaker_notes": "这是自动生成的演示文稿",
                },
                {
                    "id": 2,
                    "title": "谢谢观看",
                    "layout": "stack",
                    "key_points": "",
                    "bullet_points": [],
                    "speaker_notes": "感谢聆听",
                },
            ],
        }


# 便捷函数
def plan_ppt_from_markdown(
    markdown_content: str,
    provider: str = "deepseek",
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    便捷函数：将 Markdown 内容规划为 PPT 结构

    Args:
        markdown_content: Markdown 格式的文档内容
        provider: LLM 提供商 (deepseek/minimax/modelscope)
        options: 规划选项

    Returns:
        符合 MarpPPBuilder 的 JSON 结构
    """
    planner = ContentPlanner(provider=provider)
    return planner.plan(markdown_content, options=options)
