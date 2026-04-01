# 021 Session Workspace Store Tasks

## 当前状态

- [x] `021-topic-truth-store` 已迁移到 session workspace 数据层；当前 `context` 与资源读取都基于 active session 的 `workspace/` 目录。

## 已确认里程碑

- [x] 固定 workspace 数据层独立于 session 历史与 runtime 内部消息。
- [x] 固定 `020` 通过 `data/topic-index.json` 维护 `topic_id -> session_id` 入口映射。
- [x] 固定 `021` 的 workspace 数据层跟随 active session，最终位于 `data/sessions/<session_id>/workspace/`。
- [x] 固定当前 session 的 topic 元信息位于 `data/sessions/<session_id>/topic.json`。
- [x] 固定 workspace 数据层采用文件化存储，不引入数据库。
- [x] 固定帖子包、已选帖子、总结、文案、图片结果等 workspace 对象属于 `021` 边界。
- [x] 固定帖子 detail/raw/assets 仅作为当前 session workspace 对象的底层支撑，不并入执行层语义。
- [x] 固定 `021` 依赖 `020` 的后端服务入口，但不并入 `020` 的最小胶水层。

## 当前待办

- [x] 细化 workspace 目录结构与文件命名规则。
- [x] 将现有 `TopicTruthStore` 迁移为 session-scoped 的 workspace store，并保留最小容错读取。
- [x] 定义 `meta`、`selected_posts`、`pattern_summary`、`copy_draft`、`image_results` 的最小 schema。
- [x] 定义 `posts/<post_id>/post.json`、`raw.json`、`assets/` 的底层支撑 schema。
- [x] 实现 workspace 对象读写测试。
- [x] 定义第一波 `WorkspaceContextResponse`，包含 `candidate_posts`、`pattern_summary` 与 `copy_draft`。
- [x] 为 `candidate_posts` 详情补充完整图片数组 DTO，支持多图帖子详情翻页。
- [x] 调整后端从 session workspace store 到右侧 context DTO 的只读转换。
- [x] 保持右侧 `GET /api/topics/{topic_id}/context` 接口不变，但底层读取来源切换到 active session。
- [x] 保持资源读取路径不变，但底层资源路径切换到 session workspace。
- [x] 接通前端 `candidatePosts` 与 `patternSummary` 对新的 session workspace 真实 API 的读取。
- [x] 保持 `materials`、`collector` 继续使用 mock。
- [x] 将 `candidatePosts` 的后端读取来源改为 `posts/ + selected_posts.json`
- [x] 移除 `candidate_posts.json` 作为正式真相层文件
- [x] 为 `selected_posts.json` 增加最小写回链路：加入、移除、顺序调整
- [x] 接通 `copyDraft` 的真实读取链路，移除前端对 mock 文案的运行时依赖
- [x] 补充 `editor_images.json` 真相层与 GET/PUT API
- [x] 将 `image_results.json` 改为单列表真实读取/写入，并通过 `context` 返回
- [x] 为 assistant final message 增加图片附件元数据，支持主栏引用结果图

## 备注

- `021` 只讨论 workspace 数据结构与存储，不讨论帖子读取/下载执行流程。
- 第一波右侧真实化覆盖 `candidatePosts`、`patternSummary` 与 `copyDraft`；其中 `candidatePosts` 已支持最小已选写回。
- 详细边界与验收要求以下列文档为准：`spec.md`、`acceptance.md`
