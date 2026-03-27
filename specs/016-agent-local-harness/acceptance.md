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

## 已知限制

- 当前不是后端正式调用入口
- 当前不负责完整持久化回写
- 当前 CLI 只提供单命令 smoke 入口，不提供完整 session 管理控制台
