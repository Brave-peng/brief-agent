# PPT Agent 设计方案

## 愿景

**端到端的 PPT 自动生成 Agent**

```
日报内容 → PPT Agent → PPT 文件
```

## 核心问题

- 手动排版耗时
- 视觉风格不统一
- 配图难以获取
- 缺乏质量把控

## 设计思路

### 1. 工作流架构

```
┌─────────────────────────────────────────────────────────────┐
│                      PPT Agent                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入 → [内容分析] → [结构规划] → [视觉设计] → [内容生成]    │
│         ↓              ↓              ↓           ↓          │
│       关键信息      幻灯片大纲      模板选择      Markdown    │
│                                                             │
│                  → [图片生成] → [质量检查] → 输出            │
│                       ↓              ↓                       │
│                    配图库        Review Agent               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Agent 节点定义

| 节点 | 职责 | 输出 |
|------|------|------|
| **ContentAnalyzer** | 分析输入内容，提取关键信息 | 关键点列表 |
| **StructurePlanner** | 规划 PPT 结构，确定页数 | 幻灯片大纲 |
| **VisualDesigner** | 选择视觉风格、配色、字体 | 风格配置 |
| **SlideGenerator** | 生成每页内容（Markdown） | Slide JSON |
| **ImageGenerator** | 为每页生成配图 | 图片路径 |
| **QualityReviewer** | 检查 PPT 质量 | Review 报告 |
| **Renderer** | 渲染最终 PPT | PPTX 文件 |

### 3. 数据流

```python
# 输入格式
{
    "title": "AI 行业日报 | 2026-01-25",
    "content": "...",
    "style": "corporate",  # 可选
    "slides": 5,           # 可选
}

# 中间输出 - Slide 结构
{
    "id": 1,
    "title": "LeCun 创业公司估值 247 亿",
    "key_points": "一句话关键信息",
    "bullet_points": ["要点1", "要点2"],
    "image_prompt": "配图提示词（无文字）",
    "speaker_notes": "语音播报内容",
}

# 最终输出
{
    "pptx_path": "output/daily_report_2026-01-25.pptx",
    "review_score": 85,
    "images": ["output/images/image_1.jpg", ...],
}
```

### 4. 模板系统

```
templates/
├── default.md      # 默认商务风格（紫渐变）
├── minimal.md      # 极简白
├── corporate.md    # 商务蓝
├── gradient.md     # 渐变风格
└── dark.md         # 暗黑科技
```

每种模板支持：
- 封面样式
- 标题样式
- 列表样式
- 引用样式
- 结束页样式
- 配色方案

### 5. 图片生成

- **输入**：Slide 的 image_prompt
- **约束**：`no text, no typography, no letters, no numbers`
- **风格匹配**：
  - tech → 科技感抽象
  - business → 商务蓝几何
  - medical → 医疗分子结构
  - ai → 神经网络可视化
  - gradient → 渐变背景

### 6. 质量检查 (Review Agent)

| 维度 | 权重 | 检查项 |
|------|------|--------|
| 布局 | 30% | 间距、对齐、层次、留白 |
| 视觉 | 25% | 配色、字体、对比度 |
| 内容 | 25% | 信息密度、可读性、逻辑流 |
| 一致性 | 20% | 跨页风格统一 |

## 工具调用

```python
# 可用的 Tools
- generate_image(prompt, output_path)  # 图片生成
- json_to_marp(data, template)         # JSON 转 Marp
- render_ppt(markdown, output)         # Marp 渲染
- analyze_image(image_path)            # 图片分析
```

## 状态管理

```python
class PPTState(TypedDict):
    # 输入
    title: str
    content: str
    style: str
    slide_count: int

    # 中间状态
    key_points: list[str]
    slide_outline: list[dict]
    slides: list[Slide]
    images: list[str]

    # 输出
    pptx_path: str
    review_score: float
    review_report: str

    # 状态
    status: str  # pending/analyzing/planning/generating/reviewing/completed/failed
    error: str
```

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| LLM 调用失败 | 重试 3 次，指数退避 |
| 图片生成失败 | 使用占位图，继续生成 |
| 模板不存在 | 回退到 default 模板 |
| Review 不合格 | 自动重新生成或人工确认 |

## 扩展点

1. **多语言支持** - 自动翻译内容
2. **品牌定制** - 企业 Logo、主题色
3. **数据可视化** - 图表自动生成
4. **动画效果** - PPT 动画配置
5. **导出格式** - PDF、图片、HTML
