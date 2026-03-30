# 017 XHS Research Download Loop Tasks

## 当前状态

- [x] 已确认 `017` 是 agent 侧能力，不属于前端或纯后端 feature。
- [x] 已确认首版目标是一次调研请求后自动形成 Top 3 图文标准帖子包。
- [x] 已确认搜索与详情获取继续由 `xhs-explore` 负责。
- [x] 已确认调研类请求的编排规则由 runtime system prompt 承担。
- [x] 已确认需要新增承接结果的 xhs skill：
  - `xhs-research-ingest`
- [x] 已确认图片抓取改由 `xhs-skills` 内部 CDP 能力完成，并直接写帖子包 `assets/` 目录。

## 已确认里程碑

- [x] 固定首版帖子数为热度最高的 3 篇图文帖子。
- [x] 固定首版结果只写帖子对象，不写 `patternSummary`。
- [x] 固定图片命名为 `image-01.jpg`、`image-02.jpg`。
- [x] 固定帖子目录按需惰性创建。
- [x] 固定首版调研闭环只处理图文帖子，搜索时显式带 `--note-type 图文`。
- [x] 固定通用下载 skill 不自动更新 `selected_posts.json`。

## 当前待办

- [x] 已定义 `ingest-posts` 的输入 payload 与输出摘要。
- [x] 已在 `xhs-skills` 中新增 `xhs-research-ingest` skill 与 `ingest-posts` CLI。
- [x] 已通过 runtime system prompt 规则将 Top 3 图文详情结果交给 `xhs-research-ingest`。
- [x] 已将帖子详情、原始数据和图片通过 `ingest-posts` 写入目标 `posts` 目录。
- [x] 已允许 `xhs-research-ingest` 直接把 `posts[]` JSON 对象交给 `write_file`，不再要求模型手动先序列化成字符串。
- [x] 已为 `017` 增补自动化测试。
- [x] 已将 `ingest-posts` 收为混合落盘模式：
  - `raw_detail` 可选
  - 无 `raw_detail` 时仍可写 `post.json` 和 `assets/`
  - 有 `raw_detail` 时额外写 `raw.json`
- [x] 已将 `xhs-research-ingest` 收为通用帖子下载 skill，不再自动更新 `selected_posts.json`。
- [x] 已明确 `xhs-research-ingest` 的正式契约为通用 `posts[] + --posts-dir`，运行时的 workspace 路径仅作为当前产品调用方式。
- [x] 已明确后续总结/文案/图片流程默认只消费 `selected_posts.json` 对应帖子，而不是全部帖子包。
- [x] 已固定当前产品运行时会在 session 创建时预建 `workspace/` 与 `workspace/posts/`。
- [x] 已固定 runtime context 显式提供 `Workspace Data Root`，不再让模型自行推导 `workspace/` 路径。

## 备注

- 本 feature 的核心是“搜索采集 + xhs-skills 承接结果 + 标准帖子包落盘”的一次闭环。
- 首版不处理评论结构化、视频下载、候选列表自动导入与手动下载入口。
