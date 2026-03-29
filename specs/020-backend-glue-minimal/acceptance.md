# 020 Backend Glue Minimal Acceptance

## 手工验收

1. 启动后端服务
2. 确认服务以 FastAPI 方式启动，并允许本地前端开发源访问
3. 访问某个新的 `topic_id` 的 `GET /workspace`
4. 显式传入 `topic_title`
5. 确认首次请求会创建一个新的 session
6. 确认映射文件中写入了当前 `topic_title`
7. 确认返回结果中包含：
   - `topic_id`
   - `topic_title`
   - `session_id`
   - `messages`
   - `updated_at`
8. 检查映射文件目录
9. 确认已落盘当前 `topic_id -> active_session_id`
10. 对同一个 `topic_id` 再次请求 `GET /workspace`
11. 使用新的 `topic_title`
12. 确认返回的是同一个当前活跃 `session_id`
13. 确认映射文件中的 `topic_title` 已更新
14. 调用 `POST /api/topics/{topic_id}/runs`
15. 传入真实 `user_input` 和 `topic_title`
16. 确认后端同步返回 agent 的真实结果，而不是 mock 数据
17. 确认返回中包含：
   - `messages`
   - `last_run.final_text`
   - `last_run.tool_calls`
   - `last_run.artifacts`
18. 确认 `messages` 中只包含主栏所需的 `user/agent` 消息，不直接包含 `tool` 消息
19. 再调用 `GET /messages`
20. 确认能拿到最新消息列表
21. 调用 `POST /reset`
22. 传入 `topic_title`
23. 确认当前活跃 session 被重置
24. 确认返回的工作区视图中主栏消息已清空
25. 构造一次 runtime 或 provider 错误
26. 确认后端返回统一的 `ErrorResponse`
27. 启动前端 dev server，并配置 `VITE_API_BASE_URL`
28. 进入某个 topic 工作台页面
29. 确认主栏初次加载会请求真实 `GET /workspace`
30. 在主栏输入一条消息并发送
31. 确认页面调用真实 `POST /runs`
32. 确认主栏显示真实 agent 回复，而不是本地 `createAgentReply(...)` mock 文本
33. 确认右侧工作区仍保持现有 mock 数据
34. 若接入 `021` 的右侧 `context` 读取能力
35. 确认后端是先 resolve 当前 active session，再读取该 session 的 workspace 数据
36. 确认 `POST /reset` 后，主栏消息与右侧 workspace 数据语义保持一致

## 自动化验收

- `topic_id -> session_id` 映射文件读写测试通过
- 首次访问自动创建 session 测试通过
- 同一 `topic_id` 复用当前活跃 session 测试通过
- `topic_title` 持久化与更新测试通过
- `GET /workspace` 接口测试通过
- `POST /runs` 同步执行测试通过
- `GET /messages` 接口测试通过
- `POST /reset` 接口测试通过
- 薄 DTO 转换测试通过
- `tool` 消息不进入主栏 DTO 测试通过
- 错误 DTO 测试通过
- CORS 基本配置测试通过
- 单进程服务复用同一个 `AgentRuntime` 的集成测试通过
- 前端主栏真实 API 接线测试通过
- `VITE_API_BASE_URL` 配置测试通过
- 若组合 `021`，active session 到 workspace 数据目录的解析测试通过
- 不影响 `010~016` 既有行为的回归测试通过

## 已知限制

- 当前不提供流式输出
- 当前不提供 topic 列表管理
- 当前不提供 session 历史切换
- 当前不提供完整 session workspace 数据层
