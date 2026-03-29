# 016 Agent Local Harness

## 背景

在没有后端胶水层的情况下，需要先给主 agent 一个本地可运行入口，用于验证 runtime、session、memory、tools、skills 和 loop 是否真正能协同工作。

## 目标

- 提供本地 Python 调用入口
- 提供最小 CLI / smoke harness
- 支持复用已有 `session_id` 运行
- 支持在无 `session_id` 时基于 `topic` 创建 session 再运行
- 输出最终结果、工具调用摘要和关键产物路径
- 提供端到端联调 trace 日志能力

## 非目标

- HTTP API
- 前端联调
- GitHub skill 安装
- 文件化真相层完整回写协议

## 用户故事

- 作为开发者，我希望在没有后端的情况下先把 agent 真正跑起来。
- 作为后续实现者，我希望能快速验证当前 runtime 能否正确加载 skills、执行 loop 并复用 session 历史。

## 输入输出

- Python 入口输入：`session_id`、`user_input`、可选 `attachments`、可选 `metadata`
- CLI 输入：
  - `session_id` 或 `topic`
  - `user_input`
  - 多次 `--attachment <path>`
  - 可选 `--metadata '<json>'`
- 输出：
  - `session_id`
  - `final_text`
  - `tool_calls`
  - `artifacts`

## 约束

- 首版入口以本地 Python 接口为主
- CLI 仅作为很薄的 smoke harness，不作为正式产品入口
- CLI 采用单命令模式，通过 `python -m src.agent.local_harness run ...` 暴露
- CLI 支持两种模式：
  - 传 `session_id` 时复用已有 session
  - 不传 `session_id` 且传 `topic` 时自动创建新 session 再运行
- `session_id` 与 `topic` 互斥：
  - 同时传入时报输入错误
  - 两者都未传入时报输入错误
- `metadata` 在 CLI 中以 JSON 字符串形式传入
- 默认输出为人类可读格式
- 支持 `--json` 输出结构化结果
- 支持 `--verbose` 输出更多 tool 摘要与调试信息
- 支持 `--trace` 作为摘要 trace 开关
- 支持 `--trace-full` 作为完整 trace 开关
- CLI 退出码固定为：
  - `0` 成功
  - `1` 输入错误
  - `2` 运行失败
- skill 由 agent 自主选择，不在 harness 输入中显式指定
- local harness 默认文件系统可见范围是当前 session workspace
- local harness 不假设可访问 `/`、`/workspace` 或项目根目录
- local harness 默认 smoke 语义是 session 目录自检，而不是仓库级 smoke test
- 当 `user_input` 表述为 `smoke run` / `smoke test` 时，harness 应在送入 runtime 前将任务规范化为明确的 session 自检说明
- `smoke run` / `smoke test` 的具体任务规范化只发生在 harness 层，不属于 system prompt 的固定规则
- 执行边界、可访问目录与 `working_dir` 规则由 runtime system prompt 负责，harness 不重复注入这些稳定规则
- 默认联调应围绕：
  - 确认当前工作目录
  - 查看 session 目录
  - 必要时创建一个最小测试文件
  - 再读取并汇报结果
- 当启用 `--trace` 时，harness 必须在当前 `session workspace` 下自动创建：
  - `logs/agent-trace.log`
- trace 文件按 session 聚合：
  - 一个 session 一个固定日志文件
  - 每次 run 追加一个新的 trace block
- trace block 采用人类可读文本格式，并以明确的：
  - `===== RUN START =====`
  - `===== RUN END =====`
  分隔
- `--trace` 的详细信息写入文件，终端只输出：
  - 最终结果
  - trace 文件路径
- `--trace` 摘要模式至少记录：
  - `session_id`
  - `topic`
  - run 开始/结束时间
  - 原始 `user_input`
  - 规范化后的 `user_input`
  - `workspace_path`
  - prompt 关键 section 摘要
  - memory 检查摘要
  - loop 摘要
  - tool 调用摘要
  - `final_text`
  - `artifacts`
- `--trace-full` 在摘要模式基础上额外记录：
  - 每轮完整 `system_prompt`
  - 每轮发给模型的 `messages`
  - 每轮完整 `tool_definitions`
  - 每轮模型返回的 `content`
  - 每轮模型返回的 `tool_calls`
- trace 数据不由 harness 外层猜测拼装，而由 runtime/loop/memory 通过内部 trace sink 提供关键事件
- trace 写盘前应做最小脱敏，至少覆盖明显敏感字段名：
  - `api_key`
  - `authorization`
  - `cookie`
  - `token`
- trace 首版不要求记录：
  - provider 原始响应对象
  - 完整工具原始输出
  - 未脱敏的敏感信息

## 验收标准

- 本地可以指定一个 session 直接运行
- 本地可以在只提供 `topic` 时自动创建 session 再运行
- 能看到最终文本结果
- 能看到工具调用摘要
- 能看到关键产物路径
- 能验证可用 skills 已进入当前运行上下文
- 能验证同一 `session_id` 下历史会被复用
- `--json` 与 `--verbose` 行为清晰稳定
- `--trace` 能稳定输出单次 run 的关键中间变量摘要
- `--trace-full` 能稳定输出每轮完整 prompt/messages/tool definitions 与模型输出结果
- 默认 smoke 场景不会把项目根目录探测当作预期行为
- `smoke run` / `smoke test` 输入会被规范化成明确的 session 自检任务
- trace 文件会按 session 追加写入并可解释本次 run 的执行路径
