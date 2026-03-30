# 017 XHS Research Persist Loop

## 背景

当前系统已经具备：

- `xhs-explore` 的搜索与帖子详情获取能力
- `021` 的 session workspace 存储结构
- 前端右侧 `candidatePosts` 的真实读取与展示

但用户发起一次小红书调研请求后，系统还不能自动把热度最高的帖子沉淀成当前 session workspace 的结构化对象。也就是说，搜索、详情获取、图片下载、workspace 写入和前端可见结果之间仍缺一条端到端执行链路。

## 目标

- 定义一次小红书调研请求后的端到端执行闭环
- 让 agent 自动搜索并选取热度最高的 3 篇图文帖子
- 让 agent 获取这 3 篇图文帖子的详情数据
- 让 agent 调用纯落盘 tool，将帖子写入当前 session workspace
- 让本轮 run 返回一段文本调研结果
- 让前端在同轮交互后即可看到右侧 3 篇结构化帖子

## 非目标

- `patternSummary` 写入
- `copyDraft`、`imageResults` 写入
- 评论结构化落盘
- 视频资源下载
- 手动下载帖子按钮
- 流式下载进度
- 通用化的跨平台下载框架

## 用户故事

- 作为运营人员，我希望只发出一次调研请求，就能同时拿到一段文本调研结论和右侧工作区里的候选帖子，而不是分多轮手动整理。
- 作为系统实现者，我希望搜索采集和 workspace 落盘边界清晰：采集留在 skill，调研编排留在 system prompt，落盘留在 tool。
- 作为前端接入方，我希望本轮 run 完成后，右侧 `candidatePosts` 能立即刷新，不需要用户手动刷新页面。

## 输入输出

- 输入：
  - 用户的 xhs 调研请求
  - `xhs-explore` 返回的搜索结果与帖子详情
- 输出：
- 一段文本调研摘要
- 当前 session workspace 中新增或更新的 3 篇图文候选帖子对象

## 约束

- `017` 属于 agent 能力 feature，而不是前端或纯后端 feature
- 首版固定处理热度最高的 3 篇图文帖子
- 结构化结果首版只包含帖子对象，不写总结对象
- 搜索与详情获取继续由 `xhs-explore` 负责
- 调研请求的 Top 3 图文帖子选择、详情后落盘和最终摘要要求由 runtime system prompt 明确约束
- 新增一个纯落盘 tool：
  - `persist_xhs_posts`
- `persist_xhs_posts` 只负责：
  - resolve 当前 session
  - 创建 canonical workspace 目录
  - 下载图片
  - 写 `post.json`
  - 写 `raw.json`
  - upsert `candidate_posts.json`
- `persist_xhs_posts` 不允许自行调用小红书搜索或详情获取逻辑
- 图片下载复用：
  - `skills/xiaohongshu-skills/scripts/image_downloader.py`
- 图片文件直接写入 canonical `assets/` 目录，不经过临时目录复制
- 帖子目录按需惰性创建，不预先批量创建空目录
- 图片命名固定为：
  - `image-01.jpg`
  - `image-02.jpg`
  - 依此类推
- 首版严格只处理图文帖子：
  - 搜索阶段应显式带 `--note-type 图文`
  - 视频帖子不进入详情获取
  - 视频帖子不进入 `persist_xhs_posts`
- 若单篇帖子失败，不终止整轮任务
- 若部分图片下载失败，仍允许保留该帖的详情对象
- 本轮 run 成功后，前端必须自动刷新：
  - `GET /api/topics/{topic_id}/context`

## 执行链路

### 1. 调研采集

- agent 读取 `xhs-explore`
- 执行搜索
- 搜索时显式限制 `--note-type 图文`
- 根据热度或搜索结果优先级，选取 Top 3 篇图文帖子
- 对这 3 篇图文帖子逐条执行详情获取
- 若结果中存在视频帖子，直接跳过，不回退补视频

### 2. 结构化交接

- agent 将 Top 3 篇图文帖子的结构化详情结果传给 `persist_xhs_posts`
- 交接内容至少包含：
  - `post_id`
  - `title`
  - `url`
  - 可选 `published_at`
  - `author`
  - `content_text`
  - `metrics`
  - `image_urls`
- 可选增强字段：
  - `raw_detail`
    - 有则用于写 `raw.json`，并作为 `post.json` 的补充数据源
    - 无则不阻止落盘，tool 应优先使用显式结构化字段完成写入

### 3. workspace 落盘

- `persist_xhs_posts` resolve 当前 `session_id`
- 对每篇帖子惰性创建：
  - `data/sessions/<session_id>/workspace/posts/<post_id>/`
  - `.../assets/`
- 下载图片到 `assets/`
- 写入：
  - `post.json`
  - `raw.json`（仅当 `raw_detail` 存在时）
  - `candidate_posts.json`

### 4. 前端可见结果

- `run` 返回文本调研摘要
- 前端随后自动重新读取 `context`
- 右侧 `candidatePosts` 立即显示新增或更新的 6 篇帖子

## 内部组件

### xhs-explore

职责：

- 搜索小红书帖子
- 获取帖子详情
- 输出可用于后续落盘的详情结果

不负责：

- 调研类工作流编排
- workspace 目录创建
- 图片落盘
- `candidate_posts.json` 写入

### runtime system prompt

职责：

- 规定调研类请求应使用 `xhs-explore`
- 规定调研类请求应从搜索结果中选取 Top 3 篇图文帖子
- 规定搜索时必须显式限制 `--note-type 图文`
- 规定视频帖子在首版直接跳过
- 规定详情获取后必须调用 `persist_xhs_posts`
- 规定最终输出必须同时包含文本调研摘要和 workspace 结果

### persist_xhs_posts

职责：

- 接收结构化帖子详情
- resolve 当前 session
- 调 `SessionWorkspaceStore`
- 下载图片到 canonical `assets/`
- 写 `post.json`
- 在有 `raw_detail` 时写 `raw.json`
- upsert `candidate_posts.json`

不负责：

- 搜索帖子
- 获取帖子详情
- 生成总结对象

## 与现有 feature 的关系

- `015-agent-skills-loader`
  - 继续负责 skill 扫描与加载
- `016-agent-local-harness`
  - 可作为本地 smoke 入口验证 `017`
- `020-backend-glue-minimal`
  - 继续复用 `run` 与 `context` API
- `021-topic-truth-store`
  - 继续定义 `candidate_posts`、`post.json`、`raw.json`、`assets/` 的存储边界
- `017` 不修改 `021` schema，只负责写入这些既有对象

## 验收标准

- 一次调研请求后，agent 会自动处理 Top 3 篇图文帖子
- 本轮会返回一段文本调研摘要
- 当前 session workspace 中会新增或更新 3 篇图文候选帖子
- 每篇帖子会稳定写入：
  - `post.json`
  - `assets/`
- 若提供了 `raw_detail`，则额外写入 `raw.json`
- 右侧 `candidatePosts` 在本轮 run 后即可看到这些帖子
- 用户不需要手动刷新页面
