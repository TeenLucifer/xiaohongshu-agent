# 023 Topic Management

## 背景

当前前端工作台按 `topic_id` 路由，但 topic 列表、创建话题和删除话题仍然依赖前端 mock。`020-backend-glue-minimal` 已经建立了 `topic_id -> session_id` 的最小映射，也证明前端产品主键与 runtime 执行主键应保持分离。下一步需要把 topic 本身收成正式后端能力。

## 目标

- 固定 topic 的最小元数据模型
- 固定 `topic_id` 的生成规则
- 提供真实的 topic 列表、创建和删除 API
- 固定 topic 与 active session 的关系
- 让前端 topic 列表与工作台入口脱离 mock

## 非目标

- topic 重命名
- topic 拖拽排序
- 软删除、回收站与恢复
- 一个 topic 多 session 管理
- topic 搜索与筛选
- 右侧 workspace 数据结构
- 流式输出

## 用户故事

- 作为前端用户，我希望用自然语言标题创建话题，而不是自己构造 `topic_id`。
- 作为后端实现者，我希望由后端统一生成稳定主键，并立即建立该 topic 的 active session。
- 作为产品开发者，我希望 topic 作为前端主键独立于 runtime 的 `session_id`，但又能稳定映射到当前会话。

## 输入输出

- 输入：
  - `title`
  - 可选 `description`
- 输出：
  - `TopicListItemResponse`
  - `CreateTopicResponse`
  - `ErrorResponse`

## 约束

- 前端产品主键固定为 `topic_id`
- `topic_id` 由后端生成，不由前端生成
- `topic_id` 与 `session_id` 分离，语义不合并
- 第一版一个 `topic_id` 只对应一个当前活跃 `session_id`
- 创建 topic 时必须立即创建对应 active session，不采用懒创建
- `topic_id` 格式固定为：
  - `topic_` + ULID
- topic 元数据固定写入对应 session 目录中的：
  - `data/sessions/<session_id>/topic.json`
- active session 映射采用全局单文件：
  - `data/topic-index.json`
- topic 列表默认按 `updated_at` 倒序返回
- 删除 topic 采用硬删除
- 删除 topic 时必须同步删除：
  - `data/topic-index.json` 中的映射项
  - 当前 active session 目录
- 删除后若仍有其它 topic：
  - 前端跳转到剩余列表中的第一个 topic
- 删除后若已无 topic：
  - 前端进入空列表/空工作台状态

## 最小数据模型

### Topic Meta

- `topic_id`
- `title`
- 可选 `description`
- `created_at`
- `updated_at`

### Topic Session Mapping

- `topic_id`
- `session_id`
- `updated_at`

说明：

- `data/topic-index.json` 只承担 `topic_id -> session_id` 的轻量索引关系
- topic 标题与描述不再保存在索引中，而以 session 目录内的 `topic.json` 为准

## 内部组件

### TopicMetaStore

职责：

- 读写 `data/sessions/<session_id>/topic.json`
- 基于索引列出全部 topic 元数据
- 删除 session 目录中的 topic 元数据文件

不负责：

- 调用 runtime 创建 session
- 组装前端主栏 DTO
- 管理 session workspace 数据

### TopicSessionStore

职责：

- 读写 `data/topic-index.json`
- 管理 `topic_id -> session_id` 映射
- 返回当前 topic 的 active session

不负责：

- 生成 `topic_id`
- 管理 topic 列表

### TopicManagementService

职责：

- 创建 topic 时生成 `topic_id`
- 调用 runtime 立即创建 session
- 同时写入 `data/topic-index.json` 与 `data/sessions/<session_id>/topic.json`
- 删除 topic 时协调 topic 元数据、映射与 session 目录的硬删除
- 组装 topic 相关 DTO

不负责：

- 主栏 run 执行
- 右侧 workspace 数据层
- 流式输出

## HTTP API

### `GET /api/topics`

返回 topic 列表：

- `items`
  - `topic_id`
  - `title`
  - 可选 `description`
  - `session_id`
  - `updated_at`

约束：

- 默认按 `updated_at` 倒序

### `POST /api/topics`

输入：

- `title`
- 可选 `description`

行为：

- 生成 `topic_id`
- 立即创建 active session
- 写入 `data/sessions/<session_id>/topic.json`
- 写入 `data/topic-index.json`

返回：

- `topic_id`
- `title`
- 可选 `description`
- `session_id`
- `updated_at`

### `DELETE /api/topics/{topic_id}`

行为：

- 读取该 topic 当前 active session
- 硬删除 topic 元数据与映射
- 硬删除当前 active session 目录

返回：

- 可为最小成功结果，或返回删除后的 topic 列表摘要
- 错误时统一返回 `ErrorResponse`

## DTO 约定

### TopicListItemResponse

- `topic_id`
- `title`
- 可选 `description`
- `session_id`
- `updated_at`

### TopicListResponse

- `items`

### CreateTopicRequest

- `title`
- 可选 `description`

### CreateTopicResponse

- `topic_id`
- `title`
- 可选 `description`
- `session_id`
- `updated_at`

### ErrorResponse

- `error_code`
- `message`
- 可选 `details`

## 前端接入边界

- 前端 topic 列表应从真实 `GET /api/topics` 获取，不再长期依赖 `mockTopics`
- 创建话题时，前端只提交自然语言标题与可选描述
- 创建成功后，前端直接跳转到：
  - `/topics/{topic_id}`
- 删除当前 topic 后：
  - 若后端返回仍有剩余 topic，前端跳转到剩余第一个
  - 若已无剩余 topic，前端进入空状态
- `topic_id` 不在前端本地生成，也不从标题 slug 推导

## 与 `020/021` 的关系

- `023` 建立在 `020` 已有后端服务之上
- `020` 的 `workspace/runs/messages/reset/context` 仍按 `topic_id` 入口工作
- `023` 负责保证 topic 与 active session 的创建、列出和删除是正式能力
- `021` 的 session workspace 数据层继续跟随 active session，不因 `023` 改变目录边界

## 验收标准

- topic 列表、创建、删除具备真实后端能力
- `topic_id` 由后端生成，格式稳定
- 创建 topic 时立即创建 active session
- topic 元数据与 active session 映射都能稳定落盘
- 删除 topic 时，topic 元数据、映射与 active session 目录一起被硬删除
- 前端可以基于真实 topic API 完成列表读取、创建和删除
