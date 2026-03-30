# 021 Session Workspace Store Acceptance

## 手工验收

1. 为一个新的 `topic_id` 创建当前 active session
2. 确认目录结构符合约定
3. 确认 workspace 数据目录位于该 session 下
4. 确认 `data/sessions/<session_id>/topic.json` 存在且可读取
5. 写入 workspace 元数据
6. 确认 `meta.json` 可正常读取
7. 写入已选帖子列表
8. 确认 `selected_posts` 对象可独立读取
9. 写入单篇帖子 `post.json`、`raw.json` 与资源文件
10. 确认帖子 detail/raw/assets 可独立读取
11. 确认搜索结果可稳定引用帖子详情与资源
12. 写入模式总结
13. 确认总结对象可独立读取
14. 写入文案对象
15. 确认文案对象可独立读取
16. 写入图片结果对象
17. 确认图片结果可独立读取
18. 修改其中一个对象
19. 确认不会破坏同 session 下其它 workspace 文件
20. 新增右侧 `context` 读取接口
21. 将同一 `topic_id` 关联到 `020` 的工作区服务层
22. 确认后端先通过 `data/topic-index.json` resolve 当前 active session，再读取该 session 的 workspace 数据
23. 确认 `candidatePosts` 可由全部帖子包和 `selected_posts.json` 组装
24. 对于多图帖子，确认 `candidatePosts` 详情可返回完整图片数组
25. 对于单图帖子，确认 `candidatePosts` 详情仍可正常回退到单图展示
26. 确认 `selected` 与 `manualOrder` 可由 `selected_posts.json` 正确映射
27. 确认 `patternSummary` 可返回真实总结字段
28. 确认右侧其它 section 仍然继续使用 mock
29. 调用 `POST /reset`
30. 确认主栏消息与右侧 workspace 数据一起清空
31. 确认 session workspace 数据可被后续右侧 workspace 消费

## 自动化验收

- active session 下的 workspace 目录初始化测试通过
- session 目录内 `topic.json` 读取测试通过
- workspace 元数据读写测试通过
- 已选帖子读写测试通过
- 单篇帖子 detail/raw/assets 读写测试通过
- 总结对象读写测试通过
- 文案对象读写测试通过
- 图片结果读写测试通过
- 容错读取测试通过
- session workspace 数据层与 session 历史/记忆边界测试通过
- 右侧 workspace DTO 构建测试通过
- `GET /api/topics/{topic_id}/context` 测试通过
- session workspace 资源读取路径测试通过
- `candidatePosts` 由 `posts/ + selected_posts.json` 组装的 DTO 转换测试通过
- 多图帖子 `candidatePosts.images[]` DTO 转换测试通过
- 单图帖子回退到单项图片数组测试通过
- `patternSummary` DTO 转换测试通过
- `POST /reset` 后右侧 workspace 清空测试通过
- 前端右侧仅替换 `candidatePosts` 与 `patternSummary` 的集成测试通过

## 已知限制

- 当前不提供流式更新协议
- 当前不提供数据库或搜索索引
- 当前不直接包含前端 UI 集成实现
- 当前不定义帖子读取/下载执行流程
- 第一波右侧真实化已包含 `selected_posts.json` 的最小写回交互
- 第一波右侧真实化不包含 `copyDraft`、`imageResults`、`materials`、`collector`
- 当前 `candidatePosts` 已从 `posts/ + selected_posts.json` 组装，`candidate_posts.json` 不再作为正式真相层
