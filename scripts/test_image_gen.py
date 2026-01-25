"""
图片生成 Agent 测试
"""
from pathlib import Path
from src.agents.image_gen_workflow import (
    analyze_image_prompts,
    generate_image_agent,
    quick_generate,
    NO_TEXT_PROMPTS,
)

# 测试内容
test_content = """
LeCun创业公司AMI Labs估值247亿人民币，专注世界模型研究。
百川智能发布全球最低幻觉率医疗大模型。
百度文心5.0正式上线，展现原生全模态能力。
"""

# 输出目录
output_dir = Path("output/images_test")
output_dir.mkdir(parents=True, exist_ok=True)

def test_analyze_prompts():
    """测试提示词分析"""
    print("=" * 60)
    print("测试 1: 分析简报内容生成提示词")
    print("=" * 60)

    prompts = analyze_image_prompts(test_content, count=5)

    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}] {prompt[:80]}...")

    print(f"\n共生成 {len(prompts)} 个提示词")

    # 验证提示词中包含 "no text" 约束
    for prompt in prompts:
        if "no text" in prompt.lower() or "no typography" in prompt.lower():
            continue
        print(f"⚠️ 警告: 提示词缺少 'no text' 约束")
        break
    else:
        print("✅ 所有提示词都包含 'no text' 约束")


def test_image_gen():
    """测试图片生成"""
    import os

    print("\n" + "=" * 60)
    print("测试 2: 生成图片")
    print("=" * 60)

    # 检查 API Key
    api_key = os.getenv("MODELSCOPE_API_KEY")
    if not api_key or "your_" in api_key.lower():
        print("⚠️ 未配置 ModelScope API Key")
        print("请编辑 .env 文件: MODELSCOPE_API_KEY=xxx")
        print("\n可用命令:")
        print("  # 配置 API Key 后运行")
        print("  uv run python -c \"from src.agents.image_gen_workflow import quick_generate; quick_generate('AI technology', 'tech')\"")
        return

    styles = ["tech", "business", "medical", "ai", "gradient"]
    for i, style in enumerate(styles, 1):
        output_path = output_dir / f"image_{i}_{style}.jpg"
        print(f"\n[{style}] -> {output_path}")
        quick_generate("AI 科技新闻", style=style, output_path=str(output_path), api_key=api_key)


def show_prompts():
    """展示所有可用提示词模板"""
    print("\n" + "=" * 60)
    print("可用提示词模板")
    print("=" * 60)

    for name, prompt in NO_TEXT_PROMPTS.items():
        print(f"\n[{name}]")
        print(f"  {prompt[:60]}...")


def main():
    print("=" * 60)
    print("图片生成 Agent 测试")
    print("=" * 60)
    print(f"测试内容: {test_content[:50]}...")

    test_analyze_prompts()
    show_prompts()
    test_image_gen()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
