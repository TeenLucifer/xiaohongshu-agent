# 023 Topic Management Tasks

## 当前状态

- [x] `023-topic-management` 已完成首版实现，当前进入联调与后续扩展阶段。

## 已确认里程碑

- [x] 固定前端继续以 `topic_id` 作为产品主键。
- [x] 固定 `topic_id` 由后端生成，不由前端生成。
- [x] 固定 `topic_id` 与 `session_id` 分离。
- [x] 固定一个 `topic_id` 第一版只绑定一个当前 active session。
- [x] 固定创建 topic 时立即创建 active session。
- [x] 固定 `topic_id` 格式为 `topic_` + ULID。
- [x] 固定 topic 元数据写入对应 session 目录中的 `topic.json`。
- [x] 固定 topic 删除采用硬删除。
- [x] 固定删除后若仍有剩余 topic，前端跳转到剩余列表中的第一个。

## 当前待办

- [x] 定义 `TopicMetaStore` 的文件化读写边界。
- [x] 在后端实现 `GET /api/topics`。
- [x] 在后端实现 `POST /api/topics`。
- [x] 在后端实现 `DELETE /api/topics/{topic_id}`。
- [x] 为创建逻辑接入 runtime 的立即建 session 行为。
- [x] 实现 `data/topic-index.json` 与 session 目录内 `topic.json` 的联合落盘。
- [x] 实现删除 topic 时的硬删除协同逻辑。
- [x] 实现 topic 列表按 `updated_at` 倒序返回。
- [x] 定义 topic 相关薄 DTO 与错误 DTO。
- [x] 接通前端 topic 列表对真实 API 的读取。
- [x] 接通前端创建话题与删除话题交互。
- [x] 补齐后端与前端的自动化测试。

## 备注

- `023` 只解决 topic 列表、创建和删除，不引入重命名、排序或多 session 管理。
- `023` 不改变 `020` 的主栏 run 接口，也不改变 `021` 的 session workspace 存储边界。
- 详细边界与验收要求以下列文档为准：`spec.md`、`acceptance.md`
