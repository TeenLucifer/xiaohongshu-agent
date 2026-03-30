# 013 Agent Loop Runner Acceptance

## 手工验收

1. 初始化主 runtime、默认 tools 和 skills loader
2. 创建一个 session
3. 触发一次 `run(...)`
4. 确认 run 前先执行一次 memory consolidation 检查
5. 确认模型可以调用工具
6. 若同一轮返回多个 tool calls，确认这些 tool calls 被并发执行
7. 确认 assistant 声明 `tool_calls` 的消息先进入上下文
8. 确认 tool 结果随后按原 tool call 顺序回灌
9. 如果模型不再调用工具，确认本次执行结束
10. run 结束后确认后台再补一次 memory consolidation 检查
11. 构造持续调用工具的场景
12. 确认达到 `40` 轮后会兜底停止
13. 确认最终返回固定兜底文本
14. 构造工具失败场景
15. 确认 tool 失败被回灌为 `Error: <ExceptionType>: <message>` 形式，而不是直接打断运行
16. 检查 `RunResult.tool_calls`
17. 确认每条摘要包含：
   - `name`
   - `arguments_summary`
   - `result_summary`
18. 准备多个可用 skill
19. 确认 agent 能基于 skills summary 自主选择 skill
20. 在启用 trace 的本地联调场景下运行一次 loop
21. 确认 trace 中能看到：
   - run 开始/结束
   - 每轮发给模型的 `iteration_input`
   - 每轮模型返回的 `iteration_output`
   - 迭代轮次
   - 每轮是否有 tool calls
   - tool 调用摘要
   - 正常结束或触达最大轮数的结束原因
22. 检查 `iteration_input`
23. 确认其中包含完整 `system_prompt`、完整 `messages` 和完整 `tool_definitions`
24. 检查 `iteration_output`
25. 确认其中包含完整 `content` 和完整 `tool_calls`

## 自动化验收

- tool-calling loop 测试通过
- run 前 memory hook 测试通过
- run 后后台 memory hook 测试通过
- 无 tool call 停止测试通过
- 最大轮数兜底测试通过
- 固定兜底文本测试通过
- tool 失败回灌测试通过
- batched tool calls 并发执行测试通过
- batched tool calls 按原顺序回灌测试通过
- `RunResult.tool_calls` 摘要结构测试通过
- skill 自主选择测试通过
- loop trace 事件测试通过
- 逐轮 `iteration_input` trace 测试通过
- 逐轮 `iteration_output` trace 测试通过
- 完整 `tool_definitions` trace 测试通过

## 已知限制

- 当前不做 run-level timeout
- 当前不做结构化 run 状态模型
- 当前不负责 session/history 与长期记忆的详细治理
