# 010 Agent Runtime Foundation Acceptance

## 手工验收

1. 初始化 `AgentRuntime`
2. 确认 runtime 内部固定包含：
   - `SessionManager`
   - `ContextBuilder`
   - `SkillsLoader`
   - `ToolsRegistry`
   - `LoopRunner`
   - `Provider / ModelClient`
3. 调用 `create_session(...)`，只传 `topic` 和可选 `metadata`
4. 确认返回 `SessionSnapshot`，且 `session_id` 由 runtime 自动生成
5. 确认 `workspace_path` 由 runtime 自动生成，详细目录规则不在 `010` 内重复定义
6. 检查 `ContextBuilder.build_system_prompt()` 顺序是否为：
   - identity + runtime rules
   - bootstrap files
   - memory
   - always skills
   - skills summary
6.1 检查 `# Memory` section，确认同时包含长期记忆内容和 memory usage rules
7. 在缺少部分 bootstrap 文件时执行构建，确认不会报错
8. 检查 `build_messages()` 顺序是否为：
   - system
   - session history
   - current user message
9. 检查当前 user message 内是否包含 runtime context，且只包含时间、`session_id` 和 `workspace_path`
10. 调用 `run(...)`，确认输入不包含显式 skill 指定
11. 确认 `RunResult` 返回：
   - `session_id`
   - `final_text`
   - `tool_calls`
   - `artifacts`
12. 配置 provider 环境变量：
    - `OPENAI_API_KEY`
    - 可选 `OPENAI_BASE_URL`
    - `OPENAI_MODEL`
13. 确认 runtime 默认会尝试构造 provider / model client
14. 缺少必要 provider 配置时，确认返回清晰错误
15. 调用 `get_session_snapshot(...)`，确认只返回快照而非内部 session 实体
16. 调用 `reset_session(...)`，确认只重置会话状态，不删除工作目录
17. 对不存在的 `session_id` 调用快照或运行接口，确认抛 `SessionNotFoundError`
18. 检查 `010` 文档内容，确认没有重复定义 `011` 的 session/history 细节和 `012` 的 memory/context 细节

## 自动化验收

- runtime 初始化测试通过
- `create_session(...)` 输入边界测试通过
- `session_id` 自动生成测试通过
- `ContextBuilder.build_system_prompt()` 顺序测试通过
- bootstrap 缺失容错测试通过
- `build_messages()` 顺序测试通过
- `runtime context` 注入测试通过
- `RunResult` 结构测试通过
- 组件协作边界测试通过
- `SessionNotFoundError` 抛出测试通过
- provider config/env 测试通过
- provider 适配与响应解析测试通过
- runtime 默认 provider 构造测试通过
- provider 缺配置错误测试通过

## 已知限制

- 当前不实现 tools 具体逻辑
- 当前不实现 skills loader 具体扫描逻辑
- 当前不实现 loop 迭代细节
- 当前不重复定义 session/history 细节
- 当前不重复定义 memory/context 治理
- 当前不引入 run-level timeout、run 状态模型
- 当前 provider 首版只要求最小 OpenAI-compatible 非流式能力
