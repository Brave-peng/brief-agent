# Agent 工作记忆

## 当前项目：Brief Agent - AI 简报制片人

## 待办事项

### 高优先级

- [ ] **安装 Marp CLI**
  - 命令：`npm install -g @marp-team/marp-cli`
  - 原因：PPT 渲染需要 Marp CLI 才能生成真正的 .pptx 文件
  - 状态：当前会报错提示未安装

- [ ] **验证 DeepSeek API 配额和配置**
  - 当前 DeepSeek 可以正常工作（已测试）
  - 需要确认 API Key 配额是否充足

### 中优先级

- [ ] **配置正确的 ModelScope API 端点和模型 ID**
  - 当前问题：`qwen-turbo` 模型 ID 无效
  - 需要检查：
    - 正确的模型 ID（可能是 `qwen-turbo-latest` 或其他）
    - API 端点是否正确（当前使用 `https://api-inference.modelscope.cn/v1`）
  - 参考：ModelScope 官方文档

- [ ] **配置 MiniMax API**
  - 当前问题：返回 404
  - 需要检查：
    - API 端点是否正确
    - Group ID 是否配置

### 低优先级

- [ ] **补充测试用例**
  - 当前测试文件在 `test_content/`
  - 建议添加：
    - 单元测试（使用 pytest）
    - 集成测试（Mock LLM 调用）

- [ ] **文档更新**
  - 更新 README.md 添加 PPT 生成使用说明
  - 添加环境变量配置示例

## 已知问题

1. **Marp CLI 未安装时错误提示不清晰** ✅ 已修复
   - 修复文件：`src/render/ppt/marp_builder.py`
   - 现在会抛出清晰的 RuntimeError，提示安装命令

2. **ContentPlanner 忽略 provider 参数** ✅ 已修复
   - 修复文件：`src/agents/content_planner.py`
   - 现在正确使用传入的 provider 参数，而不是硬编码 deepseek

3. **SOCKS 代理问题** ✅ 已修复
   - 安装 `socksio` 包解决

## 常用命令

```bash
# 运行测试
uv run python main.py ppt from-md /tmp/test.md -o /tmp/out.pptx

# 使用特定 provider
uv run python main.py ppt from-md input.md --provider deepseek

# 安装 Marp CLI
npm install -g @marp-team/marp-cli
```

## 相关文件

- PPT 构建器：`src/render/ppt/marp_builder.py`
- 内容规划器：`src/agents/content_planner.py`
- CLI 入口：`src/cli/ppt.py`
- LLM 管理器：`src/llm/manager.py`

---

*最后更新：2026-01-29*
