# 013 Agent Loop Runner

## 背景

主 agent 需要真正进入基于 tool-calling 的执行循环。该循环应尽量贴近 `nanobot` 的停止模型和工具回灌方式，但适配当前项目的 `session_id` 模型和 agent 自主选择 skill 的方式。

## 目标

- 建立基于 tool-calling 的 agent loop
- 固定 `max_iterations = 40`
- 在 run 前执行一次 memory consolidation 检查
- 在 run 后后台补一次 memory consolidation 检查
- 在模型返回 tool calls 时执行工具并回灌结果
- 在模型不再返回 tool calls 时结束
- 当达到最大轮数时返回兜底文本
- 最终输出风格偏执行结果报告

## 非目标

- Session / SessionManager 的详细设计
- 长期记忆与上下文窗口治理
- run-level timeout
- 结构化 run 状态模型
- 后端任务系统
- 前端日志协议

## 用户故事

- 作为主 agent，我希望在一次运行中持续调用工具直到任务完成，而不是只做单轮回复。
- 作为实现者，我希望 loop 与 session/history、memory/context 管理解耦，避免把运行时和记忆机制混在一起。

## 输入输出

- 输入：`session_id`、用户输入、历史消息、可用 tools、已加载 skills 摘要
- 输出：最终文本结果、工具调用摘要、追加后的消息历史

## 约束

- loop 停止模型贴近 `nanobot`
  - 模型本轮不再返回 tool call，则结束
  - 达到最大轮数，则兜底停止
- `max_iterations = 40`
- 所有 skill 都允许 loop
- skill 由 agent 基于 skills summary 自主选择
- run 前固定调用一次 memory consolidation 检查
- run 后固定后台调用一次 memory consolidation 检查
- 同一轮 assistant 返回的多个 tool calls 并发执行
- 并发执行的结果按原 tool call 顺序回灌
- assistant/tool 消息追加顺序固定为：
  - 先追加声明 `tool_calls` 的 assistant 消息
  - 再追加对应的 tool 结果消息
- tool 普通失败应转成 tool result 回灌，而不是直接打断 loop
- 不增加整次 run 的总 timeout
- 不单独设计 run 状态模型
- loop 应支持向 harness 暴露内部 trace 事件，用于联调日志
- trace 事件应暴露完整逐轮输入输出，但不暴露 provider 原始对象或思维链

## Loop 责任边界

`013` 只负责一次 run 的执行链：

1. 取 `session.get_history(...)`
2. 调 `ContextBuilder.build_messages(...)`
3. 调模型
4. 执行 tool calls
5. 回灌 tool 结果
6. 直到无 tool call 或达到最大轮数
7. 保存 session
8. 触发后台 memory consolidation 检查
9. 在关键节点向可选 trace sink 上报事件

`013` 不负责：

- session/history 详细协议
- memory 预算与文件格式
- tools 具体实现
- skills 扫描与安装细节
- trace 文件落盘格式与 CLI 输出策略

## Tool 调用规则

- 同一轮 assistant 可返回多个 tool calls
- 多个 tool calls 采用并发执行
- 即使某个 tool 抛出异常，也不直接中断整轮 loop
- tool 异常需要转成字符串结果回灌，格式固定为：
  - `Error: <ExceptionType>: <message>`
- 当启用 trace 时，loop 至少应上报：
  - run 开始/结束
  - 每轮发给模型的 `iteration_input`
  - 每轮模型返回的 `iteration_output`
  - 当前迭代轮次
  - 每轮是否有 tool calls
  - 每个 tool call 的摘要结果
  - 是正常结束还是触达最大轮数
- `iteration_input` 至少包含：
  - 完整 `system_prompt`
  - 完整 `messages`
  - 完整 `tool_definitions`
- `iteration_output` 至少包含：
  - 完整 `content`
  - 完整 `tool_calls`

## 最大轮数兜底

当达到 `max_iterations = 40` 且任务仍未完成时，返回固定兜底文本：

`已达到最大工具调用轮数（40），任务仍未完成。建议将任务拆分后重试。`

## RunResult.tool_calls

`RunResult.tool_calls` 来自本次 run 中实际发生的工具调用摘要。

每条摘要最小字段固定为：

- `name`
- `arguments_summary`
- `result_summary`

约束：

- 不暴露 provider 原始 tool call 对象
- 不回传完整原始 stdout 或大块工具结果
- 只返回面向调试和 harness 的轻量摘要

## 验收标准

- loop 能在工具调用与模型响应之间正常往返
- run 前会触发一次 memory consolidation 检查
- run 后会后台补一次 memory consolidation 检查
- 当模型不再发 tool call 时能正常结束
- 达到 `max_iterations = 40` 时能兜底停止
- 触顶时返回固定兜底文本
- 工具结果能稳定回灌到消息上下文
- tool 失败时能以错误结果形式回灌，而不是直接中断整个运行
- 同一轮多个 tool calls 能并发执行并按原顺序回灌
- `RunResult.tool_calls` 采用轻量摘要结构
- agent 能基于 skills summary 自主选择 skill
- loop 的关键事件可被 harness 用于生成联调 trace
