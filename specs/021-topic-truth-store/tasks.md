# 021 Session Workspace Store Tasks

## 当前状态

- [x] `021-topic-truth-store` 已迁移到 session workspace 数据层；当前 `context` 与资源读取都基于 active session 的 `workspace/` 目录。

## 已确认里程碑

- [x] 固定 workspace 数据层独立于 session 历史与 runtime 内部消息。
- [x] 固定 `020` 继续维护 `topic_id -> active_session_id` 入口映射。
- [x] 固定 `021` 的 workspace 数据层跟随 active session，最终位于 `data/sessions/<session_id>/workspace/`。
- [x] 固定 workspace 数据层采用文件化存储，不引入数据库。
- [x] 固定候选帖子、已选帖子、总结、文案、图片结果等 workspace 对象属于 `021` 边界。
- [x] 固定帖子 detail/raw/assets 仅作为当前 session workspace 对象的底层支撑，不并入执行层语义。
- [x] 固定 `021` 依赖 `020` 的后端服务入口，但不并入 `020` 的最小胶水层。

## 当前待办

- [x] 细化 workspace 目录结构与文件命名规则。
- [x] 将现有 `TopicTruthStore` 迁移为 session-scoped 的 workspace store，并保留最小容错读取。
- [x] 定义 `meta`、`candidate_posts`、`selected_posts`、`pattern_summary`、`copy_draft`、`image_results` 的最小 schema。
- [x] 定义 `posts/<post_id>/post.json`、`raw.json`、`assets/` 的底层支撑 schema。
- [x] 实现 workspace 对象读写测试。
- [x] 定义第一波 `WorkspaceContextResponse`，只包含 `candidate_posts` 与 `pattern_summary`。
- [x] 为 `candidate_posts` 详情补充完整图片数组 DTO，支持多图帖子详情翻页。
- [x] 调整后端从 session workspace store 到右侧 context DTO 的只读转换。
- [x] 保持右侧 `GET /api/topics/{topic_id}/context` 接口不变，但底层读取来源切换到 active session。
- [x] 保持资源读取路径不变，但底层资源路径切换到 session workspace。
- [x] 接通前端 `candidatePosts` 与 `patternSummary` 对新的 session workspace 真实 API 的读取。
- [x] 保持 `materials`、`collector`、`copyDraft`、`imageResults` 继续使用 mock。

## 备注

- `021` 只讨论 workspace 数据结构与存储，不讨论帖子读取/下载执行流程。
- 第一波右侧真实化只覆盖 `candidatePosts` 与 `patternSummary`，且只读。
- 详细边界与验收要求以下列文档为准：`spec.md`、`acceptance.md`
