# 020 Backend Glue Minimal Acceptance

## 手工验收

1. 启动后端服务
2. 确认服务以 FastAPI 方式启动，并允许本地前端开发源访问
3. 访问某个新的 `topic_id` 的 `GET /workspace`
4. 显式传入 `topic_title`
5. 确认首次请求会创建一个新的 session
6. 确认 `data/topic-index.json` 中写入了当前 `topic_id -> session_id`
7. 确认返回结果中包含：
   - `topic_id`
   - `topic_title`
   - `session_id`
   - `messages`
   - `updated_at`
8. 检查 `data/topic-index.json`
9. 确认已落盘当前 `topic_id -> session_id`
10. 检查 `data/sessions/<session_id>/topic.json`
11. 确认 topic 标题与描述以 session 目录内的 `topic.json` 为准
12. 对同一个 `topic_id` 再次请求 `GET /workspace`
13. 使用新的 `topic_title`
14. 确认返回的是同一个当前活跃 `session_id`
15. 确认 session 目录内 `topic.json` 中的标题已更新
16. 调用 `POST /api/topics/{topic_id}/runs`
17. 传入真实 `user_input` 和 `topic_title`
18. 确认后端同步返回 agent 的真实结果，而不是 mock 数据
19. 确认返回中包含：
   - `messages`
   - `last_run.final_text`
   - `last_run.tool_calls`
   - `last_run.artifacts`
20. 确认 `messages` 中只包含主栏所需的 `user/agent` 消息，不直接包含 `tool` 消息
21. 再调用 `GET /messages`
22. 确认能拿到最新消息列表
23. 调用 `POST /reset`
24. 传入 `topic_title`
25. 确认当前活跃 session 被重置
26. 确认返回的工作区视图中主栏消息已清空
27. 构造一次 runtime 或 provider 错误
28. 确认后端返回统一的 `ErrorResponse`
29. 启动前端 dev server，并配置 `VITE_API_BASE_URL`
30. 进入某个 topic 工作台页面
31. 确认主栏初次加载会请求真实 `GET /workspace`
32. 在主栏输入一条消息并发送
33. 确认页面调用真实 `POST /runs`
34. 确认主栏显示真实 agent 回复，而不是本地 `createAgentReply(...)` mock 文本
35. 若组合 `021` 的右侧 `context` 读取能力
36. 确认右侧 `candidatePosts` / `patternSummary` 已可走真实读取
37. 确认后端是先 resolve 当前 active session，再读取该 session 的 workspace 数据
38. 确认 `POST /reset` 后，主栏消息与右侧 workspace 数据语义保持一致

## 自动化验收

- `data/topic-index.json` 读写测试通过
- 首次访问自动创建 session 测试通过
- 同一 `topic_id` 复用当前活跃 session 测试通过
- session 目录内 `topic.json` 读写与更新测试通过
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
