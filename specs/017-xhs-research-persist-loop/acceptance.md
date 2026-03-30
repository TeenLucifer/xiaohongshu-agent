# 017 XHS Research Persist Loop Acceptance

## 手工验收

1. 启动后端与前端
2. 进入任意一个 topic 工作台
3. 在主栏输入一次小红书调研请求
4. 确认 agent 会执行搜索流程
5. 确认 agent 搜索时显式限制图文帖子（`--note-type 图文`）
6. 确认 agent 会继续处理热度最高的 3 篇图文帖子
7. 确认视频帖子不会进入详情获取和落盘列表
8. 确认本轮最终返回一段文本调研摘要
9. 确认右侧 `candidatePosts` 在本轮完成后自动出现最多 3 篇图文帖子
10. 打开其中任意一篇帖子详情
11. 确认能看到正文与图片
12. 对于多图帖子，确认详情中能正常逐张浏览
13. 检查当前 session 目录
14. 确认存在：
    - `workspace/candidate_posts.json`
    - `workspace/posts/<post_id>/post.json`
    - `workspace/posts/<post_id>/assets/`
15. 若本轮提供了 `raw_detail`，确认存在：
    - `workspace/posts/<post_id>/raw.json`
16. 确认图片文件命名为：
    - `image-01.jpg`
    - `image-02.jpg`
17. 若其中一篇帖子详情失败，确认其余帖子仍然正常落盘
18. 若某篇帖子部分图片失败，确认该帖子仍保留详情对象
19. 若某篇帖子没有 `raw_detail`，确认该帖子仍然会写入 `post.json`、`candidate_posts.json` 和图片资源
20. 确认用户不需要手动刷新页面即可看到右侧结果

## 自动化验收

- Top 3 图文帖子筛选测试通过
- runtime system prompt 对调研类请求的“仅图文 / Top 3 / `persist_xhs_posts`”规则注入测试通过
- `xhs-explore` 详情结果到 `persist_xhs_posts` 的交接测试通过
- `persist_xhs_posts` 写入 `candidate_posts.json` 测试通过
- 无 `raw_detail` 时 `post.json` / `candidate_posts.json` / `assets/` 写入测试通过
- 有 `raw_detail` 时 `raw.json` 写入测试通过
- 图片命名顺序测试通过
- 视频帖子跳过测试通过
- 已存在 candidate 的 `selected` / `manual_order` 保留测试通过
- 单篇详情失败不中断整轮测试通过
- 部分图片下载失败仍保留详情测试通过
- `run` 后自动刷新 `context` 测试通过
- 右侧 `candidatePosts` 同轮可见测试通过

## 已知限制

- 当前不写 `patternSummary`
- 当前不处理评论结构化落盘
- 当前不处理视频资源下载
- 当前不提供手动下载帖子入口
