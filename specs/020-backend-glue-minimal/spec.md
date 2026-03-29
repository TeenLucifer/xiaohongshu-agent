# 020 Backend Glue Minimal

## 背景

前端当前已经有按 `topic_id` 组织的工作台原型，agent 侧也已经有可运行的 `AgentRuntime`。两者之间还缺一层最小后端胶水，用于把前端的 topic 语义映射到 runtime 的 session 语义，并暴露稳定的同步 API。

## 目标

- 提供一个基于 FastAPI 的单进程 Python 后端服务
- 服务启动时长期持有一个 `AgentRuntime`
- 固定 `topic_id -> active_session_id` 的最小映射规则
- 为前端主栏对话提供同步 API
- 固定后端薄 DTO 边界
- 固定最小错误返回结构
- 与前端主栏一起完成第一版真实 API 接线

## 非目标

- 完整 session workspace 数据层
- 流式输出
- topic 列表管理
- session 历史切换
- 数据库
- 队列、异步任务、取消与重试
- 右侧工作区真实数据回写
- 前端静态资源托管

## 用户故事

- 作为前端接入方，我希望按 `topic_id` 调后端，而不是直接理解 `session_id`。
- 作为后端实现者，我希望复用现有 `AgentRuntime`，只增加一层最小的 topic/session 胶水。
- 作为产品开发者，我希望先打通主栏真实对话，再逐步接右侧工作区和流式能力。

## 输入输出

- 输入：
  - `topic_id`
  - `user_input`
  - 可选 `attachments`
  - 可选 `metadata`
- 输出：
  - `WorkspaceResponse`
  - `RunResponse`
  - `MessagesResponse`
  - `ResetResponse`
  - `ErrorResponse`

## 约束

- 后端是单进程 Python API 服务
- 第一版后端框架固定为 FastAPI
- 后端服务代码位于顶层 `src/backend/`
- `src/agent/` 只保留 runtime 内核：
  - runtime
  - session
  - memory
  - loop
  - tools
  - skills
- 后端属于包裹 `AgentRuntime` 的外层接入层，不并入 `agent` 包内部
- 服务进程内长期持有一个 `AgentRuntime`
- 前端按 `topic_id` 调后端，不按 `topic` 文本或 `session_id` 调 runtime
- 一个 `topic_id` 第一版只绑定一个当前活跃 `session_id`
- 后端必须维护文件化映射：
  - `topic_id -> active_session_id`
- 首次访问某个 `topic_id` 时：
  - 若无映射，则创建新 session
  - `topic_title` 由前端每次请求显式传入
  - session 的 `topic` 使用当前请求中的 `topic_title`
- 同一 `topic_id` 再次访问时：
  - 默认复用当前活跃 session
  - 若当前请求携带新的 `topic_title`，则应更新映射文件中的 `topic_title`
- `POST /runs` 采用同步执行：
  - 请求阻塞直到 `runtime.run(...)` 返回
- 第一版后端只服务前端主栏对话
- 第一版前端接入范围只包含主栏，不包含右侧工作区真实化
- 第一版主栏 API 不负责候选帖子、总结、文案、图片结果等 session workspace 对象
- 后端返回薄 DTO，不直接暴露 runtime 内部模型
- 错误返回采用最小清晰结构，不做复杂任务状态机
- 本地开发拓扑固定为：
  - 前端 Vite dev server
  - 独立后端 API 服务
- 后端需提供最小 CORS 支持，允许本地前端开发源调用

## 内部组件

### TopicSessionStore

职责：

- 读取某个 `topic_id` 当前活跃 `session_id`
- 首次访问时创建映射
- 更新映射文件
- 读取 topic 基本元信息

不负责：

- 调用 runtime 执行 run
- 组装 API DTO
- 管理 session workspace 对象

### BackendAppService

职责：

- resolve `topic_id` 对应的当前 session
- 调用 `AgentRuntime`
- 将 runtime 结果转换为后端 DTO
- 组装错误返回

不负责：

- 持久化 session workspace 数据层
- 流式输出
- 复杂任务调度

## 映射存储

- 映射采用文件化持久化
- 建议目录规则：
  - `data/topics/<topic_id>/session.json`
- 文件至少保存：
- `topic_id`
- `active_session_id`
- `topic_title`
- `updated_at`
- 映射读取失败时：
  - 记录日志
  - 允许按“无映射”处理并重新创建

## HTTP API

### `GET /api/topics/{topic_id}/workspace`

输入：

- `topic_title`

返回最小工作区视图：

- `topic_id`
- `topic_title`
- `session_id`
- `messages`
- `updated_at`
- 可选 `last_run`

### `POST /api/topics/{topic_id}/runs`

输入：

- `user_input`
- `topic_title`
- 可选 `attachments`
- 可选 `metadata`

行为：

- resolve/create 当前 session
- 同步调用 `runtime.run(...)`
- 读取最新消息列表

返回：

- `topic_id`
- `topic_title`
- `session_id`
- `messages`
- `last_run.final_text`
- `last_run.tool_calls`
- `last_run.artifacts`
- `updated_at`

### `GET /api/topics/{topic_id}/messages`

输入：

- `topic_title`

返回当前活跃 session 的消息列表。

### `POST /api/topics/{topic_id}/reset`

输入：

- `topic_title`

重置当前活跃 session，并返回重置后的最小工作区视图。

## DTO 约定

### Message DTO

- `id`
- `role`
- `text`
- `time`
- 可选 `agent_name`

约束：

- 主栏聊天消息只暴露：
  - `user`
  - `agent`
- runtime 的 `tool` 消息不直接进入前端主栏消息列表
- `user` 消息映射为前端 `user`
- `assistant` 消息映射为前端 `agent`
- `id` 可由后端按 `session_id + message_index` 稳定生成

### WorkspaceResponse

- `topic_id`
- `topic_title`
- `session_id`
- `messages`
- `updated_at`
- 可选 `last_run`

### RunResponse

- `topic_id`
- `topic_title`
- `session_id`
- `messages`
- `last_run`
- `updated_at`

### MessagesResponse

- `topic_id`
- `session_id`
- `messages`
- `updated_at`

### ResetResponse

- `topic_id`
- `topic_title`
- `session_id`
- `messages`
- `updated_at`

### ErrorResponse

- `error_code`
- `message`
- 可选 `details`

## 前端接入边界

- 020 实现阶段需要同步接通前端主栏到真实后端 API
- 前端新增最小 API client，用于：
  - 获取 workspace
  - 发起同步 run
  - 获取消息列表
  - 重置当前 topic
- 前端右侧工作区继续使用现有 mock 数据
- 前端主栏不再使用本地 `createAgentReply(...)` mock 回复
- 前端 API base URL 通过环境变量提供：
  - `VITE_API_BASE_URL`
- 若后续组合 `021` 的右侧 `context` 读取能力：
  - `020` 先 resolve 当前 active session
  - 再从该 session 的 workspace 数据目录读取右侧数据
  - 不再单独定义跨 session 的 `data/topics/<topic_id>/` 真相层
- 本地开发可默认回退到：
  - `http://127.0.0.1:8000`

## 与现有 runtime 的关系

- 后端实现位于顶层 `src/backend/`，不位于 `src/agent/` 包内
- `AgentRuntime` 对外接口保持不变：
  - `create_session(...)`
  - `get_session_snapshot(...)`
  - `reset_session(...)`
  - `run(...)`
- 后端只是新增一层 topic/session 胶水，不修改 `010~016` 的既有边界

## 验收标准

- 后端可按 `topic_id` 创建并复用 session
- 同一 `topic_id` 默认对应一个当前活跃 session
- `GET /workspace` 能返回主栏所需的最小工作区 DTO
- `POST /runs` 能同步返回真实 agent 回复
- `GET /messages` 能返回当前消息列表
- `POST /reset` 能重置当前会话并返回新的工作区视图
- 错误能以统一 DTO 返回
- 前端主栏可仅依赖这一层后端 API 替换当前 mock 对话数据
- 右侧工作区在 020 中继续保持 mock，不受本轮实现影响
