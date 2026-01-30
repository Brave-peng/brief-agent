# Brief Agent

> **个人知识中枢** —— 多源信息汇入、Agent智能处理、多模态内容输出
> 
> 一个NotebookLM-inspired的本地化知识管理平台，支持RSS订阅、本地文件等多源输入，通过RAG检索与Agent协作，输出对话问答、闪卡、PPT、日报等多种形态。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        输出层 (Output)                            │
│   🗣️ 对话问答    📇 闪卡(Anki)    📊 PPT    📰 日报/周报          │
├─────────────────────────────────────────────────────────────────┤
│                      处理层 (Processing)                         │
│   🧠 Router意图识别    🔍 RAG检索    🤖 Agent协作    💾 记忆管理    │
├─────────────────────────────────────────────────────────────────┤
│                        输入层 (Input)                           │
│   📡 RSS订阅    📁 本地文件    🌐 网页链接                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心能力

| 能力 | 状态 | 说明 |
|------|------|------|
| **多源采集** | ✅ | RSS定时抓取、本地文件夹监控、网页解析 |
| **RAG检索** | ✅ | ChromaDB向量存储，支持语义搜索与摘要索引 |
| **Agent协作** | ✅ | 多Agent工作流（分析→编剧→结构化→审核） |
| **PPT生成** | ✅ | 内容分析→结构规划→视觉设计→Marp渲染 |
| **图片生成** | ✅ | ModelScope ZImage中文提示词生成 |
| **TTS音频** | ✅ | DashScope/MiniMax双引擎 |
| **闪卡生成** | ⏳ | Anki格式导出，间隔重复学习 |
| **交互模式** | ⏳ | Rich美化CLI，支持对话式交互 |

---

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repo-url>
cd brief-agent

# 安装依赖 (需要Python 3.11+)
uv sync

# 安装Marp CLI用于PPT生成
npm install -g @marp-team/marp-cli
```

### 2. 配置

```bash
# 复制环境变量模板
cp env.example .env

# 编辑.env，填入你的API Keys
vim .env

# 编辑配置文件
vim config.yaml
```

### 3. 运行

```bash
# 抓取RSS并生成日报
uv run main.py rss fetch

# 从Markdown生成PPT
uv run main.py ppt from-md input.md -o output.pptx --provider deepseek

# 从Markdown生成PPT
uv run main.py ppt from-md input.md -o output.pptx

# 查看所有命令
uv run main.py --help
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **编排** | LangGraph (多Agent工作流) |
| **LLM** | DeepSeek / MiniMax / ModelScope |
| **RAG** | ChromaDB + 自研分层检索 |
| **数据** | SQLite (SQLModel) |
| **CLI** | Typer + Rich |
| **渲染** | Marp (Markdown → PPTX) |
| **图像** | ModelScope ZImage |
| **音频** | DashScope / MiniMax TTS |

---

## 路线图

### Phase 1: 基础架构 ✅
- [x] **RSS采集** - 定时抓取、本地文件监控
- [x] **RAG检索** - ChromaDB向量存储，语义搜索
- [x] **分层检索** - 摘要索引 + 细节索引双轨制
- [ ] **Router节点** - 统一入口，意图识别与任务分发 ⏳

### Phase 2: 内容生产 ✅
- [x] **动态PPT** - 内容分析→结构规划→视觉设计→Marp渲染
- [x] **图片生成** - ModelScope Z-Image中文提示词生成
- [x] **TTS音频** - DashScope/MiniMax双引擎
- [ ] **视频管线** - Marp渲染→视频合成 🚧
- [ ] **自我纠错** - 质量检查循环，自动重试 ⏳

### Phase 3: 交互体验 ⏳
- [ ] **交互式Shell** - Rich库美化，对话式交互
- [ ] **记忆管理** - 实体提取，持久化记忆
- [ ] **闪卡技能** - Anki格式导出，间隔重复

### Phase 4: 工程化 🚧
- [x] **Token管理** - 费用统计，LangSmith链路追踪
- [ ] **CI/CD** - 自动化测试，沙盒环境
- [ ] **多开Agent** - 并发优化，任务队列

---

## 开发

```bash
# 代码检查
ruff check src/
ruff check --fix src/

# 类型检查
mypy src/

# 运行测试
uv run pytest tests/
```

---

## 相关项目

- [NotebookLM](https://notebooklm.google.com/) - Google的AI笔记本产品，本项目的主要灵感来源
- [PPTAgent](https://arxiv.org/abs/2501.03936) - PPT自动生成论文参考

---

## License

GNU GENERAL PUBLIC LICENSE Version 3

---

> 💡 **提示**: 本项目目前处于活跃开发阶段，API和架构可能会有较大变动。欢迎提交Issue和PR！
