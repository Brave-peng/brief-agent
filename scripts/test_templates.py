"""
Marp 模板效果测试
生成各模板的示例 PPT
"""
import json
from pathlib import Path
from src.render.ppt.marp_builder import MarpPPBuilder
from src.render.ppt.json_to_marp import json_to_marp_markdown

# 测试数据
test_data = {
    "title": "AI 行业日报 | 2026-01-25",
    "slides": [
        {
            "id": 1,
            "title": "LeCun 创业公司估值 247 亿",
            "key_points": "图灵奖得主 Yann LeCun 创立 AMI Labs，专注世界模型研究",
            "bullet_points": [
                "估值 30 亿欧元（约 247 亿人民币）",
                "采用开源路线，总部设在巴黎",
                "将在纽约、蒙特利尔、新加坡设立分支",
                "谢赛宁可能加入担任首席科学家"
            ],
            "speaker_notes": "图灵奖得主 LeCun 创立新公司，估值高达 247 亿人民币"
        },
        {
            "id": 2,
            "title": "百川智能发布医疗大模型",
            "key_points": "全球最低幻觉率医疗大模型正式发布",
            "bullet_points": [
                "幻觉率指标达到行业领先水平",
                "专注医疗场景深度优化",
                "已与多家三甲医院达成合作"
            ],
            "speaker_notes": "百川智能在医疗 AI 领域取得重大突破"
        },
        {
            "id": 3,
            "title": "百度文心 5.0 正式上线",
            "key_points": "原生全模态能力，展现强大多模态处理能力",
            "bullet_points": [
                "支持文本、图像、视频、音频统一理解",
                "推理效率提升 50%",
                "开放 API 供开发者使用"
            ],
            "speaker_notes": "百度文心大模型再升级，全模态能力引关注"
        }
    ]
}

# 模板列表
templates = ["default", "minimal", "corporate", "gradient", "dark"]

# 输出目录
output_dir = Path("output/templates_test")
output_dir.mkdir(parents=True, exist_ok=True)

def test_template(template_name: str):
    """测试单个模板"""
    print(f"\n{'='*50}")
    print(f"测试模板: {template_name}")
    print(f"{'='*50}")

    try:
        builder = MarpPPBuilder(
            data=test_data,
            provider="deepseek",
            template=template_name
        )

        # 打印生成的 Markdown 前 30 行
        from src.render.ppt.json_to_marp import json_to_marp_markdown
        marp_content = json_to_marp_markdown(test_data, template=template_name)
        print(f"\n生成的 Markdown 内容（前30行）：")
        print("-" * 50)
        for i, line in enumerate(marp_content.split('\n')[:30], 1):
            print(f"{i:3}: {line}")
        print("-" * 50)

        # 输出路径
        output_path = str(output_dir / f"daily_report_{template_name}.pptx")

        # 构建
        builder.build(output_path)

        # 同时生成 markdown 查看内容
        marp_content = json_to_marp_markdown(test_data)
        md_path = output_dir / f"daily_report_{template_name}.md"
        md_path.write_text(marp_content, encoding="utf-8")
        print(f"Markdown 已生成: {md_path}")

        # 检查文件
        pptx_path = Path(output_path)
        if pptx_path.exists():
            print(f"✅ PPTX 已生成: {output_path} ({pptx_path.stat().st_size / 1024:.1f} KB)")
        else:
            print(f"⚠️ PPTX 未生成（可能缺少 Marp CLI）")
            print(f"✅ Markdown 已生成: {md_path}")

        return True

    except Exception as e:
        print(f"❌ 模板 {template_name} 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Marp 模板效果测试")
    print("=" * 60)
    print(f"测试数据: {test_data['title']}")
    print(f"幻灯片数量: {len(test_data['slides'])}")
    print(f"输出目录: {output_dir}")
    print(f"测试模板: {', '.join(templates)}")

    results = []
    for template in templates:
        result = test_template(template)
        results.append((template, result))

    # 汇总
    print(f"\n{'='*60}")
    print("测试汇总")
    print(f"{'='*60}")
    for template, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {template:12} {status}")

    # 说明
    print(f"\n{'='*60}")
    print("使用说明")
    print(f"{'='*60}")
    print("""
1. 安装 Marp CLI: npm install -g @marp-team/marp-cli
2. 使用模板:
   from src.render.ppt.marp_builder import MarpPPBuilder

   builder = MarpPPBuilder(
       data=data,
       template="minimal"  # 或 corporate, gradient, dark
   )
   builder.build("output.pptx")

3. 查看 Markdown 效果:
   cat output/templates_test/daily_report_*.md
""")


if __name__ == "__main__":
    main()
