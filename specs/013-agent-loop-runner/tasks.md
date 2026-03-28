# 013 Agent Loop Runner Tasks

## 当前任务分组

- [x] `013-A`：实现主 agent loop
  建立模型调用、工具调用、消息回灌和 session 保存的最小闭环。
- [x] `013-B`：固定 loop 停止逻辑
  对齐 `nanobot` 的“无 tool call 即结束”和最大轮数固定兜底文本。
- [x] `013-C`：接入工具结果回灌
  让 tool 执行结果以 `tool` 消息形式回灌到当前消息上下文，并固定 assistant/tool 追加顺序。
- [x] `013-D`：接入 skill 自主选择
  让 agent 基于 skills summary 自主决定是否读取和使用 skill。
- [x] `013-E`：接入 memory hook
  固定 run 前检查和 run 后后台补一次 consolidation 的调度时机。
- [x] `013-F`：固定 batched tool calls 执行策略
  让同一轮多个 tool calls 并发执行，并按原顺序回灌结果。
- [x] `013-G`：统一结果输出结构
  让最终回复偏执行结果报告，并固定 `RunResult.tool_calls` 的轻量摘要结构。

## 测试与验收

- [x] tool-calling loop 测试
- [x] run 前 memory hook 测试
- [x] run 后后台 memory hook 测试
- [x] 无 tool call 停止测试
- [x] `max_iterations = 20` 兜底测试
- [x] tool 失败回灌测试
- [x] batched tool calls 并发执行测试
- [x] batched tool calls 按原顺序回灌测试
- [x] 固定兜底文本测试
- [x] `RunResult.tool_calls` 摘要结构测试
- [x] skill 自主选择测试

## 实现收口

- [x] 主 loop 已落地
- [x] 工具回灌路径已落地
- [x] memory hook 已落地
- [x] `RunResult.tool_calls` 摘要结构已落地
- [x] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成
- 依赖 `011-session-history-core` 已完成
- 依赖 `012-context-memory-core` 已完成
- 依赖 `014-agent-tools-core` 已完成
- 依赖 `015-agent-skills-loader` 已完成

## 备注

- 当前不承载 session/history 的详细协议，也不承载长期记忆机制。
