# 016 Agent Local Harness Tasks

## 当前任务分组

- [x] `016-A`：建立本地 runtime 调用入口
  提供最小 Python 调用接口，串起 runtime、session 和 agent 执行。
- [x] `016-B`：建立最小 CLI / smoke harness
  采用单命令模式，支持用命令方式传入 `session_id` 或 `topic` 加 `user_input`。
- [x] `016-C`：统一本地输出格式
  输出最终文本结果、工具调用摘要和关键产物路径，并支持 `--json`。
- [x] `016-D`：建立最小 smoke 验证链路
  用一组真实 skills 验证 runtime、tools、skills 和 loop 的协同。
- [x] `016-E`：实现 CLI 参数校验与退出码
  校验 `session_id/topic` 互斥关系、`metadata` JSON 字符串和退出码策略。
- [x] `016-F`：实现详细输出模式
  提供 `--verbose` 以输出更多 tool 摘要与调试信息。
- [ ] `016-G`：规范化 smoke run 语义
  在 harness 中将 `smoke run` / `smoke test` 转换为明确的 session 目录自检任务说明。

## 测试与验收

- [x] 本地 Python 入口测试
- [x] CLI / harness 参数解析测试
- [x] `session_id/topic` 互斥校验测试
- [x] `metadata` JSON 解析测试
- [x] 输出格式测试
- [x] `--json` 输出测试
- [x] `--verbose` 输出测试
- [x] 退出码测试
- [x] 最小 smoke run 测试
- [ ] `smoke run` 语义规范化测试

## 实现收口

- [x] 本地 harness 已落地
- [x] smoke 验证链路已落地
- [ ] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成
- 依赖 `011-session-history-core` 已完成
- 依赖 `012-context-memory-core` 已完成
- 依赖 `013-agent-loop-runner` 已完成
- 依赖 `014-agent-tools-core` 已完成
- 依赖 `015-agent-skills-loader` 已完成

## 备注

- 当前不替代后端，只作为本地验证入口。
- CLI 不是正式产品入口，只服务本地 smoke 与调试。
