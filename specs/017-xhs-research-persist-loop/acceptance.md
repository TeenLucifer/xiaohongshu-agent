# 017 XHS Research Download Loop Acceptance

## 手工验收

1. 启动后端与前端，或使用 `local_harness`
2. 发起一次小红书调研请求
3. 确认 agent 会执行搜索流程
4. 确认 agent 搜索时显式限制图文帖子（`--note-type 图文`）
5. 确认 agent 会继续处理热度最高的 3 篇图文帖子
6. 确认视频帖子不会进入详情获取和下载列表
7. 确认本轮最终返回一段文本调研摘要
8. 检查目标 `posts` 目录
9. 确认存在：
   - `posts/<post_id>/post.json`
   - `posts/<post_id>/assets/`
10. 若本轮提供了 `raw_detail`，确认存在：
    - `posts/<post_id>/raw.json`
11. 确认图片文件命名为：
    - `image-01.jpg`
    - `image-02.jpg`
12. 确认不会自动写入 `selected_posts.json`
13. 确认 `xhs-research-ingest` 的输入输出语义保持通用：
    - 输入为 `posts[] + --posts-dir`
    - 不要求 skill 理解 session/workspace 业务语义
14. 确认当前产品运行时仍会把 `--posts-dir` 指向当前 session 根目录下的 `workspace/posts`
15. 确认 runtime context 中直接提供：
    - `Session Root Path`
    - `Workspace Data Root`
16. 确认新建 session 后，目录中已存在：
    - `workspace/`
    - `workspace/posts/`
17. 确认后续若进入总结/文案/图片流程，默认只消费 `selected_posts.json` 对应帖子
18. 若其中一篇帖子详情失败，确认其余帖子仍然正常落盘
19. 若某篇帖子部分图片失败，确认该帖子仍保留详情对象
20. 若某篇帖子没有 `raw_detail`，确认该帖子仍然会写入 `post.json` 和图片资源

## 自动化验收

- Top 3 图文帖子筛选测试通过
- runtime system prompt 对调研类请求的“仅图文 / Top 3 / `xhs-research-ingest`”规则注入测试通过
- `xhs-explore` 详情结果到 `xhs-research-ingest` 的交接测试通过
- `write_file` 可直接接收 `posts[]` JSON 对象并成功写出临时 payload 文件
- `ingest-posts` 写入帖子包目录测试通过
- `ingest-posts` 通用 `posts[] + --posts-dir` 契约测试通过
- 无 `raw_detail` 时 `post.json` / `assets/` 写入测试通过
- 有 `raw_detail` 时 `raw.json` 写入测试通过
- 图片命名顺序测试通过
- 视频帖子跳过测试通过
- 不自动生成 `selected_posts.json` 测试通过
- 单篇详情失败不中断整轮测试通过
- 部分图片下载失败仍保留详情测试通过
- 浏览器导航 + `<img>` 截图保存图片测试通过

## 已知限制

- 当前不写 `patternSummary`
- 当前不处理评论结构化落盘
- 当前不处理视频资源下载
- 当前不自动更新 `selected_posts`
- 当前帖子包下载完成后，仍需用户手动加入已选，后续流程不默认消费全量帖子包
- 当前不提供手动下载帖子入口
