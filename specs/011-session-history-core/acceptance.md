# 011 Session History Core Acceptance

## 手工验收

1. 创建一个 session
2. 确认 `session_id` 为 `uuid4`
3. 确认 `last_consolidated = 0`
4. 确认 `workspace_path` 目录已实际创建
5. 确认 `Session` 字段符合约定
6. 确认 `SessionSnapshot` 不包含额外统计字段
7. 向 session 追加 `user`、`assistant`、`tool` 三类消息
8. 确认不会出现额外消息类型
9. 检查持久化消息，确认保留：
   - `tool_calls`
   - `tool_call_id`
   - `name`
10. 写入超长 tool 结果
11. 确认入 session 时结果被截断
12. 调用 `get_history(...)`
13. 确认返回的是从 `last_consolidated` 开始的合法历史切片，不会以前置孤立 tool 结果开头
14. 在不手工建目录的情况下调用 `list_dir(".")`
15. 确认 session workspace 上的目录访问可以正常工作
16. 触发 session 保存与加载
17. 确认 session 以 `jsonl` 保存，且第一行为 metadata，后续每行是一条 message
18. 确认 metadata 行中包含 `last_consolidated`
19. 连续两次保存同一 session，确认文件按整份 session 被重写
20. 模拟一次 consolidation 成功，确认 `last_consolidated` 前移
21. 模拟一次 consolidation 失败，确认 `last_consolidated` 不前移
22. 模拟 session 已存在但 `workspace_path` 目录缺失，再触发加载
23. 确认加载成功后会补建 `workspace_path`
24. 调用 `reset_session(...)`
25. 确认只清空 `messages`、重置游标，并保留 `session_id/topic/workspace_path/metadata`
26. 确认 `SessionSnapshot` 返回轻量快照而非内部实体
27. 构造损坏的 session 文件
28. 确认加载失败时记录日志并返回 `None`

## 自动化验收

- `Session` 结构测试通过
- `SessionSnapshot` 结构测试通过
- `session_id = uuid4` 测试通过
- `last_consolidated` 默认值测试通过
- `SessionManager` 职责边界测试通过
- session 创建即落盘 workspace 目录测试通过
- 消息追加测试通过
- `get_history(...)` 按游标返回合法切片测试通过
- tool 消息截断测试通过
- `jsonl` 结构测试通过
- `last_consolidated` 持久化读写测试通过
- `save` 重写策略测试通过
- session 加载成功时 workspace 缺失补建测试通过
- `reset_session(...)` 行为测试通过
- consolidation 失败时游标不前移测试通过
- session 加载失败容错测试通过

## 已知限制

- 当前不处理长期记忆
- 当前不处理超上下文窗口后的摘要或压缩
