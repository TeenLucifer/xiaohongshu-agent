# 023 Topic Management Acceptance

## 手工验收

1. 启动后端服务
2. 调用 `GET /api/topics`
3. 确认返回当前全部 topic 列表
4. 确认列表按 `updated_at` 倒序
5. 调用 `POST /api/topics`
6. 传入自然语言 `title`，可选传入 `description`
7. 确认返回结果中包含：
   - `topic_id`
   - `title`
   - `session_id`
   - `updated_at`
8. 确认 `topic_id` 格式为 `topic_` + ULID
9. 检查 `data/topics/<topic_id>/topic.json`
10. 确认 topic 元数据已落盘
11. 检查 `data/topics/<topic_id>/session.json`
12. 确认 active session 映射已落盘
13. 检查 `data/sessions/<session_id>/`
14. 确认创建 topic 时已立即创建 session 目录
15. 前端打开 topic 列表页
16. 确认列表来自真实 `GET /api/topics`，而不是仅依赖 mock
17. 在前端创建一个新话题
18. 确认创建成功后页面跳转到 `/topics/{topic_id}`
19. 在该 topic 工作台中确认主栏与右侧仍能按既有 `020/021` 语义工作
20. 删除一个存在的 topic
21. 确认 `topic.json`、`session.json` 与对应 session 目录被硬删除
22. 若仍有剩余 topic，确认前端跳转到剩余列表中的第一个
23. 若已无剩余 topic，确认前端进入空状态
24. 删除一个不存在的 topic
25. 确认后端返回统一的 `ErrorResponse`

## 自动化验收

- `topic_id` 生成为 `topic_` + ULID 的测试通过
- `POST /api/topics` 会立即创建 active session 的测试通过
- `topic.json` 与 `session.json` 联合落盘测试通过
- `GET /api/topics` 倒序返回测试通过
- `DELETE /api/topics/{topic_id}` 会删除 topic 元数据、映射和 session 目录的测试通过
- 删除不存在 topic 的错误 DTO 测试通过
- 前端 topic 列表真实 API 接线测试通过
- 前端创建话题后跳转测试通过
- 前端删除当前 topic 后的跳转或空状态测试通过
- 不影响 `020` 主栏接口与 `021` session workspace 行为的回归测试通过

## 已知限制

- 当前不支持 topic 重命名
- 当前不支持 topic 排序或拖拽
- 当前不支持一个 topic 多 session 管理
- 当前不支持软删除与恢复
