# 017 XHS Research Persist Loop Tasks

## 当前状态

- [x] 已确认 `017` 是 agent 侧能力，不属于前端或纯后端 feature。
- [x] 已确认首版目标是一次调研请求后自动形成 Top 3 图文结构化帖子结果。
- [x] 已确认搜索与详情获取继续由 `xhs-explore` 负责。
- [x] 已确认调研类请求的编排规则由 runtime system prompt 承担。
- [x] 已确认需要新增纯落盘 tool：
  - `persist_xhs_posts`
- [x] 已确认图片下载复用 `image_downloader.py`，并直接写 canonical `assets/` 目录。

## 已确认里程碑

- [x] 固定首版帖子数为热度最高的 3 篇图文帖子。
- [x] 固定首版结果只写帖子对象，不写 `patternSummary`。
- [x] 固定图片命名为 `image-01.jpg`、`image-02.jpg`。
- [x] 固定帖子目录按需惰性创建。
- [x] 固定前端在 `run` 成功后自动刷新 `context`。
- [x] 固定首版调研闭环只处理图文帖子，搜索时显式带 `--note-type 图文`。

## 当前待办

- [x] 已定义 `persist_xhs_posts` 的内部输入 schema 与输出摘要。
- [x] 已在 agent runtime / loop 执行链路中接入 `persist_xhs_posts`。
- [x] 已通过 runtime system prompt 规则将 Top 3 图文详情结果交给 `persist_xhs_posts`。
- [x] 已将帖子详情、原始数据和图片写入 `SessionWorkspaceStore`。
- [x] 已实现 `candidate_posts.json` 的 upsert 规则，并保留 `selected` / `manual_order`。
- [x] 已在前端 `run` 成功后自动重新请求 `context`。
- [x] 已为 `017` 增补自动化测试。
- [x] 已将 `persist_xhs_posts` 调整为混合落盘模式：
  - `raw_detail` 可选
  - 无 `raw_detail` 时仍可写 `post.json`、`candidate_posts.json` 和 `assets/`
  - 有 `raw_detail` 时额外写 `raw.json`

## 备注

- 本 feature 的核心是“搜索采集 + workspace 落盘 + 前端即时可见”的一次闭环。
- 首版不处理评论结构化、视频下载与手动下载入口。
