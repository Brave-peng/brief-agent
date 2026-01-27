# Brief Agent

企业级多模态知识内生 Agent 平台 (AI 简报制片人) - 基于 LangGraph 的多模态内容自动生成与分发系统。

## 功能特性

- **多源数据采集** - RSS 订阅管理，自动定时抓取
- **AI 智能分析** - 多 Agent 协作（分析师、编剧、结构化专家、审核员）
- **短视频脚本生成** - 将资讯转化为具备短视频逻辑的脚本
- **视频渲染输出** - JSON 生产协议驱动 FFmpeg/MoviePy 渲染
- **RAG 向量化检索** - 基于 ChromaDB 的语义搜索与知识增强
- **日报/周报生成** - 自动汇总生成结构化报告
- **定时任务调度** - 支持按需配置定时执行

## 快速开始

### 1. 环境准备

```bash
# 使用 uv 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
```

### 2. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 3. 编辑配置文件

```bash
vim config.yaml
```

主要配置项说明：

```yaml
# LLM 配置
llm:
  default: "minimax"  # 默认 provider
  providers:
    minimax:
      api_key: "${MINIMAX_API_KEY}"  # 从环境变量读取
      base_url: "https://api.minimaxi.com/v1"
      model: "abab6.5s-chat"
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"
      model: "deepseek-chat"
    modelscope:
      api_key: "${MODELSCOPE_API_KEY}"
      model: "qwen-turbo"

# RSS 订阅源
rss:
  feeds:
    - url: "https://example.com/feed.xml"
      name: "订阅源名称"
  fetch_interval: 3600  # 抓取间隔（秒）

# 数据库配置
database:
  path: "data/sqlite/rss.db"

# 向量数据库配置
vector_db:
  path: "data/chroma"
  collection: "rss_articles"
```

### 4. 运行程序

```bash
# 使用 uv 运行
uv run python main.py fetch              # 抓取 RSS
uv run python main.py parse              # 解析文章
uv run python main.py report 2026-01-11  # 生成日报
```

## 项目结构

```
brief-agent/
├── main.py              # CLI 入口 (typer)
├── config.yaml          # 配置文件
├── env.example          # 环境变量示例
├── pyproject.toml       # 项目配置
├── uv.lock              # uv 锁定文件
├── README.md            # 项目文档
├── CLAUDE.md            # AI 助手文档
├── src/
│   ├── __init__.py      # 包初始化
│   ├── config.py        # 配置加载
│   ├── models/          # 外部模型 API
│   │   ├── llm/         # 文本 LLM (MiniMax/DeepSeek/ModelScope)
│   │   │   ├── __init__.py
│   │   │   └── manager.py
│   │   ├── image/       # 图片生成 (ModelScope Z-Image-Turbo)
│   │   │   ├── __init__.py
│   │   │   ├── image_modelscope.py
│   │   │   ├── oss.py
│   │   │   └── aliyun/
│   │   └── audio/       # TTS 音频 (DashScope/MiniMax)
│   │       ├── __init__.py
│   │       ├── generator.py
│   │       ├── dashscope.py
│   │       └── minimax.py
│   ├── prompts/         # 提示词模板
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
│   │   ├── db.py        # SQLite (SQLModel)
│   │   ├── logger.py    # loguru 日志
│   │   └── vector_store.py  # ChromaDB
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
├── tests/               # 测试文件
├── docs/                # 设计文档
└── data/                # 数据目录（自动创建）
    ├── sqlite/          # SQLite 数据库
    ├── chroma/          # ChromaDB 向量库
    └── logs/            # 日志文件
```

## 配置说明

### LLM Provider

支持配置多个 LLM 提供商：

- **MiniMax** - `minimax` provider
- **ModelScope (Qwen)** - `modelscope` provider
- **DeepSeek** - `deepseek` provider

### RSS 订阅

在 `config.yaml` 的 `rss.feeds` 中添加订阅源：

```yaml
rss:
  feeds:
    - url: "https://news.example.com/rss"
      name: "新闻资讯"
    - url: "https://tech.example.com/feed"
      name: "科技动态"
```

### 定时任务

```yaml
scheduler:
  timezone: "Asia/Shanghai"
  report_daily_hour: 8     # 日报生成时间（小时）
  report_weekly_hour: 9    # 周报生成时间（周一的小时）
```

## Claude Code Skills

项目包含多个 Claude Code Skills，提升 AI 协作效率：

### 1. code-review - 代码审查
```bash
# 当需要对代码进行审查时，Claude 会自动加载此 skill
# 触发词: "review", "审核", "审查"
```
- 安全性检查（密钥、注入、权限）
- 正确性检查（空值、异常、资源泄漏）
- 性能检查（冗余、低效）
- FastAPI 专项审查

### 2. test-gen - 测试生成
```bash
# 生成核心业务逻辑的 pytest 测试
# 触发词: "生成测试", "写测试", "test"
```
- 只测核心路径（Agents > Services > Models > Render）
- 生成 pytest 测试代码
- 包含 Mock 策略

### 3. visual-review - 视觉审查
```bash
# 审查 PPT/Marp 生成效果
# 触发词: "看看效果", "视觉审查", "设计点评"
```
- 布局结构分析
- 视觉层次评估
- 内容呈现优化
- 设计一致性检查

---

## 开发

### 代码风格

```bash
# 运行 lint
ruff check src/

# 自动修复
ruff check --fix src/

# 类型检查
mypy src/
```

### 运行测试

```bash
uv run pytest tests/
```

## Roadmap

### 已完成

| 状态 | 功能 | 说明 |
|------|------|------|
| ✅ | 日报提示词优化 | 今日概览 + 来源链接保留 |
| ✅ | Marp 模板风格库 | 5 种视觉风格（default/minimal/corporate/gradient/dark） |
| ✅ | 视觉图片生成 Agent | ModelScope ZImage + 中文提示词 + 速率限制 |
| ✅ | 代码结构重构 | models/ 目录统一管理外部模型 API |

### 开发中

| 状态 | 功能 | 说明 |
|------|------|------|
| ⏳ | PPT Agent路线 | 端到端 PPT 自动生成（内容分析→结构规划→视觉设计→图片生成→渲染输出）,参考paper:[PPTAgent](https://arxiv.org/abs/2501.03936)|
| ⏳ | Token 管理系统 | 费用统计、链路追踪、可视化，考虑使用LangSmith|
| ⏳ | 视觉评估 Review Agent | PPT/图片质量评审 |

### 规划中

- CI/CD 沙盒自动测试
- 多开 Agent 提效方案

## License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007
