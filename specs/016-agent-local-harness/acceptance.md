# 016 Agent Local Harness Acceptance

## 手工验收

1. 准备一个可用 skill
2. 创建一个 session
3. 使用本地 Python 入口传入 `session_id` 和 `user_input`
4. 触发一次 agent 执行
5. 确认可以得到最终文本结果
6. 确认输出中包含工具调用摘要
7. 确认输出中包含关键产物路径
8. 使用相同 `session_id` 再执行一次
9. 确认会话历史可以复用
10. 使用命令行传入 `session_id` 重复上述过程
11. 确认 CLI / harness 行为与 Python 入口一致
12. 使用命令行只传 `topic` 和 `user_input`
13. 确认 harness 会先创建 session 再运行
14. 同时传入 `session_id` 和 `topic`
15. 确认返回输入错误且退出码为 `1`
16. 使用 `--metadata '{"source":"smoke"}'` 运行
17. 确认 metadata 能被正确解析
18. 使用 `--json` 运行
19. 确认输出为结构化结果，包含 `session_id / final_text / tool_calls / artifacts`
20. 使用 `--verbose` 运行
21. 确认会显示更多 tool 摘要与调试信息
22. 使用 `--trace` 运行一次本地 harness
23. 确认当前 `session workspace` 下自动创建：
   - `logs/agent-trace.log`
24. 确认终端输出中包含 trace 文件路径
25. 打开 `agent-trace.log`
26. 确认本次 run 以 `RUN START / RUN END` block 追加写入
27. 确认 block 至少包含：
   - `session_id`
   - 原始 `user_input`
   - 规范化后的 `user_input`
   - `workspace_path`
   - prompt 关键 section 摘要
   - memory 检查摘要
   - loop 摘要
   - tool 调用摘要
   - `final_text`
28. 使用 `--trace-full` 运行一次本地 harness
29. 确认 block 中额外包含：
   - 每轮完整 `system_prompt`
   - 每轮发给模型的 `messages`
   - 每轮完整 `tool_definitions`
   - 每轮模型返回的 `content`
   - 每轮模型返回的 `tool_calls`
30. 使用 `smoke run` 或 `smoke test` 作为输入运行
31. 确认 harness 会将其转成明确的 session 自检任务，而不是原样把模糊文本直接交给模型
32. 在空 session 目录中运行上述输入
33. 确认默认行为是目录自检与最小文件读写闭环，而不是因为“没有代码”直接判定 smoke 无法执行
34. 使用同一 `session_id` 再次运行并开启 `--trace`
35. 确认 `agent-trace.log` 中追加了新的 run block，而不是覆盖旧内容
36. 在 trace 中构造明显敏感字段名
37. 确认 `api_key`、`authorization`、`cookie`、`token` 等值被最小脱敏，而不是原样落盘

## 自动化验收

- 本地 Python 入口测试通过
- CLI / harness 参数解析测试通过
- `session_id/topic` 互斥校验测试通过
- `metadata` JSON 解析测试通过
- 输出格式测试通过
- `--json` 输出测试通过
- `--verbose` 输出测试通过
- 退出码测试通过
- 最小 smoke run 测试通过
- `smoke run` 语义规范化测试通过
- `--trace` 参数解析测试通过
- `--trace-full` 参数解析测试通过
- trace 文件创建与追加测试通过
- trace 路径输出测试通过
- trace block 内容摘要测试通过
- 逐轮 prompt/messages trace 测试通过
- 完整 `system_prompt` trace 测试通过
- 完整 `tool_definitions` trace 测试通过
- 逐轮模型输出 trace 测试通过
- trace 最小脱敏测试通过

## 已知限制

- 当前不是后端正式调用入口
- 当前不负责完整持久化回写
- 当前 CLI 只提供单命令 smoke 入口，不提供完整 session 管理控制台
- 当前 trace 首版只提供人类可读文本日志，不提供结构化 JSON trace
