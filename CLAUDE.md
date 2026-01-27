# Brief Agent

企业级多模态知识内生 Agent 平台 (AI 简报制片人 | Insights-to-Video Pipeline)

---

## 项目愿景

**无人值守的数字化内容分发中心**

```
RSS/多源数据 → Agent 智能分析 → PPT/视频脚本 → JSON 生产协议 → 渲染输出 → 自动分发
```

### PPT Agent 工作流

```
输入 → 内容分析 → 结构规划 → 视觉设计 → 幻灯片生成 → 图片生成 → 质量检查 → 输出
```

### 核心节点

| 节点 | 职责 |
|------|------|
| ContentAnalyzer | 分析输入内容，提取关键信息 |
| StructurePlanner | 规划 PPT 结构，确定页数 |
| VisualDesigner | 选择视觉风格、配色、字体 |
| SlideGenerator | 生成每页内容（Markdown/Slide JSON） |
| ImageGenerator | 为每页生成配图（无文字约束） |
| QualityReviewer | 检查 PPT 质量（布局/视觉/内容/一致性） |
| Renderer | 渲染最终 PPT (Marp → PPTX) |
```

---

## 目录结构

```
brief-agent/
├── main.py              # CLI 入口 (typer)
├── config.yaml          # 主配置
├── pyproject.toml       # 依赖管理
├── env.example          # 环境变量示例
├── uv.lock              # uv 锁定文件
├── src/
│   ├── __init__.py      # 包初始化
│   ├── config.py        # 配置加载模块
│   ├── models/          # 外部模型 API
│   │   ├── __init__.py
│   │   ├── llm/         # 文本 LLM 管理
│   │   │   ├── __init__.py
│   │   │   └── manager.py     # 统一管理 (MiniMax/DeepSeek/ModelScope)
│   │   ├── image/       # 图片生成
│   │   │   ├── __init__.py
│   │   │   ├── image_modelscope.py  # ModelScope Z-Image-Turbo
│   │   │   ├── oss.py               # OSS 上传
│   │   │   └── aliyun/              # 阿里云图片生成
│   │   └── audio/       # TTS 音频
│   │       ├── __init__.py
│   │       ├── generator.py   # 统一生成器
│   │       ├── minimax.py     # MiniMax TTS
│   │       └── dashscope.py   # DashScope CosyVoice
│   ├── agents/          # Agent 层 (LangGraph)
│   │   ├── __init__.py
│   │   ├── article_parser_langgraph.py  # 文章解析工作流
│   │   ├── report_workflow.py           # 报告生成工作流
│   │   └── image_gen_workflow.py        # 图片生成 Agent
│   ├── services/        # 业务服务
│   │   ├── __init__.py
│   │   └── rss.py       # RSS 抓取
│   ├── storage/         # 数据存储
│   │   ├── __init__.py
│   │   ├── db.py        # SQLModel (SQLite)
│   │   ├── vector_store.py  # ChromaDB
│   │   └── logger.py    # loguru 日志
│   └── render/          # 渲染层（本地输出）
│       ├── __init__.py
│       └── ppt/         # PPT 构建
│           ├── __init__.py
│           ├── base.py         # 抽象基类
│           ├── builder.py      # 直接渲染构建器
│           ├── marp_builder.py # Marp Markdown 构建器
│           ├── json_to_marp.py # JSON 转 Marp
│           └── templates/      # 模板
│               ├── default.md
│               ├── minimal.md
│               ├── corporate.md
│               ├── gradient.md
│               └── dark.md
├── tests/
├── scripts/
├── docs/                   # 设计文档
│   └── ppt_agent_design.md  # PPT Agent 设计方案
└── data/                # 数据库、向量库、日志
```

---

## 常用命令

```bash
cd brief-agent

# 安装依赖
uv sync

# CLI 命令
uv run python main.py fetch              # 抓取 RSS
uv run python main.py parse              # 解析文章
uv run python main.py report 2026-01-11  # 生成日报

# 图片生成
uv run python -m src.models.image.image_modelscope gen "提示词" -o img.jpg
uv run python -m src.models.image.image_modelscope batch prompts.txt -w 3

# 开发
uv run pytest tests/                     # 测试
ruff check src/                          # 检查
ruff check --fix src/                    # 自动修复
mypy src/                                # 类型检查
```

---

## Claude Code Skills

项目定义了多个 Claude Code Skills，提升 AI 协作效率：

### 1. code-review - 代码审查
```
触发词: "review", "审核", "审查"

功能:
- 安全性 (30%): 密钥泄露、注入攻击、依赖漏洞
- 正确性 (30%): 空值风险、异常处理、资源泄漏
- 性能 (20%): 冗余计算、N+1 查询
- 可读性 (10%): 命名、注释、结构
- 规范 (10%): 类型、文档、风格

FastAPI 专项:
- 路径参数验证、响应模型
- Pydantic V2 语法
- 依赖注入安全
- CORS 配置
```

### 2. test-gen - 测试生成
```
触发词: "生成测试", "写测试", "test"

功能:
- 优先级: Agents > Services > Storage > Models > Render
- 只生成核心路径测试
- pytest 框架
- 包含 Mock 策略 (LLM/RSS/文件/DB)
```

### 3. visual-review - 视觉审查
```
触发词: "看看效果", "视觉审查", "设计点评"

功能:
- 支持: .pptx, .md, .png/.jpg
- 维度: 布局(30%), 视觉(25%), 内容(25%), 一致性(20%)
- 输出: 评分 + 优点 + 改进建议
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 编排 | LangGraph |
| LLM | MiniMax, ModelScope (Qwen), DeepSeek |
| 图片生成 | ModelScope Z-Image-Turbo |
| TTS 音频 | DashScope CosyVoice, MiniMax |
| 数据库 | SQLite (SQLModel) + ChromaDB |
| RSS | feedparser + httpx |
| 渲染 | FFmpeg / MoviePy / python-pptx / Marp CLI |
| 运维 | LangSmith, APScheduler |

---

## 开发规范

- **CLI**: typer 框架
- **包管理**: uv
- **类型注解**: 所有公开函数必须标注
- **日志**: loguru（不用 print）
- **错误处理**: 直接 raise，不捕获
- **配置**: 业务配置用 pyproject.toml，密钥用 .env
- **模型调用**: 统一放在 `models/` 目录，避免循环依赖

---

## 环境变量

```
MINIMAX_API_KEY      # MiniMax LLM + TTS
MODELSCOPE_API_KEY   # ModelScope/Qwen LLM + Z-Image 图片生成
DEEPSEEK_API_KEY     # DeepSeek LLM
DASHSCOPE_API_KEY    # DashScope 音频
LANGCHAIN_API_KEY    # LangSmith 追踪
REDIS_URL            # 任务队列（可选）
OSS_*                # 阿里云 OSS（可选）
```

---

## 人机协作规范

### 交互模板

每次交互遵循以下结构：

**上一步** - 简述已完成的工作

**下一步** - 列出具体步骤

**待确认** - 需要用户决策的事项

**测试** - 最小测试命令 + 预期结果

### 测试原则

- 只测核心路径
- 一条命令验证
- 明确预期输出

### 危险操作

以下需用户明确同意后再执行：
- 删除文件、数据库重置
- 回滚、强制覆盖代码
- 外部请求（发布、部署）

### 示例

```
## 上一步
完成 RSS 抓取模块重构。

## 下一步
1. 修复文章解析编码问题
2. 更新 config.yaml

## 待确认
重试次数从 3 次改为 5 次？

## 测试
uv run python main.py fetch --dry-run
预期：显示抓取计划但不实际请求
```

---

## 模块导入规范

```python
# 模型调用（外部 API）
from src.models.llm import LLMManager
from src.models.image import generate_image
from src.models.audio import AudioGenerator

# Agent 编排
from src.agents.report_workflow import generate_daily_report
from src.agents.image_gen_workflow import generate_image_agent

# 业务服务
from src.services.rss import RSSFetcher

# 本地渲染
from src.render.ppt import DirectPPBuilder, MarpPPBuilder

# 配置和工具
from src.config import load_config
from src.storage import get_db
```
