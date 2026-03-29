# 020 Backend Glue Minimal Tasks

## 当前状态

- [x] `020-backend-glue-minimal` 已完成首版实现，当前处于联调与后续扩展阶段。

## 已确认里程碑

- [x] 固定前端按 `topic_id` 调后端，不直接按 `session_id` 调 runtime。
- [x] 固定一个 `topic_id` 默认绑定一个当前活跃 `session_id`。
- [x] 固定后端为基于 FastAPI 的单进程 Python 服务，并长期持有一个 `AgentRuntime`。
- [x] 固定 `topic_id -> session_id` 采用文件化映射，并收口到 `data/topic-index.json`。
- [x] 固定第一版 `run` 为同步执行，不做流式、不做完整 topic 真相层。
- [x] 固定第一版只服务主栏对话，并通过 4 个最小接口暴露能力。
- [x] 固定 `topic_title` 由前端每次请求显式传入。
- [x] 固定本地开发为前端 dev server + 独立后端 API 服务。
- [x] 固定前端主栏与 020 一起接入真实 API，右侧工作区继续保留 mock。
- [x] 固定 `tool` 消息不进入前端主栏聊天消息。

## 当前待办

- [x] 在顶层 `src/backend/` 定义后端服务入口与应用服务层骨架。
- [x] 实现 `TopicSessionStore` 文件化映射。
- [x] 实现 `GET /workspace`、`POST /runs`、`GET /messages`、`POST /reset`。
- [x] 实现 topic/session 到薄 DTO 的转换逻辑。
- [x] 实现统一错误 DTO 与最小错误处理策略。
- [x] 实现最小 CORS 与前端 API base URL 约定。
- [x] 补齐映射层、API 层与 runtime 集成测试。
- [x] 接通前端主栏对真实后端 API 的最小依赖准备与页面替换。

## 备注

- 详细边界与验收要求以下列文档为准：`spec.md`、`acceptance.md`
- 若组合 `021` 的右侧读取能力，底层应读取当前 active session 的 `data/sessions/<session_id>/workspace/` 数据，而不是独立的 topic 目录。
