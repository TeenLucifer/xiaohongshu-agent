# 017 XHS Research Download Loop

## 背景

当前系统已经具备：

- `xhs-explore` 的搜索与帖子详情获取能力
- `xhs-skills` 内部可复用的 Chrome/CDP 能力
- `021` 已确定的帖子目录结构：
  - `posts/<post_id>/post.json`
  - `posts/<post_id>/raw.json`
  - `posts/<post_id>/assets/...`

但用户发起一次小红书调研请求后，系统还不能稳定把结果沉淀成可复用的**标准帖子包**。首版需要先打通：

- 搜索
- 详情获取
- 图片抓取
- 帖子包落盘

不在本轮解决候选列表自动导入、总结生成和视频下载。

## 目标

- 定义一次小红书调研请求后的端到端执行闭环
- 让 agent 自动搜索并选取热度最高的 3 篇图文帖子
- 让 agent 获取这 3 篇图文帖子的详情数据
- 让 agent 调用承接结果的 xhs skill，将帖子下载成标准帖子包
- 让本轮 run 返回一段文本调研结果
- 让目标 `posts` 目录中得到 3 个可复用的帖子目录

## 非目标

- `selected_posts.json` 自动更新
- `patternSummary`、`copyDraft`、`imageResults` 写入
- 评论结构化落盘
- 视频资源下载
- 手动下载帖子按钮
- 流式下载进度

## 用户故事

- 作为运营人员，我希望一次调研请求后，就能得到一段文本结论和一组本地帖子包，方便后续手动挑选。
- 作为运营人员，我希望后续总结、文案和图片等流程只基于我手动加入已选的帖子，而不是默认消费全部帖子包。
- 作为系统实现者，我希望搜索采集和帖子包落盘边界清晰：采集留在 `xhs-explore`，图片抓取留在 `xhs-skills`，不把 CDP 细节泄漏到 agent/tool 层。

## 输入输出

- 输入：
  - 用户的小红书调研请求
  - `xhs-explore` 返回的搜索结果与帖子详情
- 输出：
  - 一段文本调研摘要
  - 目标 `posts` 目录中的 3 个图文帖子包

## 约束

- `017` 属于 agent 能力 feature，而不是前端或纯后端 feature
- 首版固定处理热度最高的 3 篇图文帖子
- 搜索与详情获取继续由 `xhs-explore` 负责
- 调研请求的 Top 3 图文帖子选择和最终摘要要求由 runtime system prompt 明确约束
- 新增一个承接结果的 xhs skill：
  - `xhs-research-ingest`
- `xhs-research-ingest` 通过 CLI 命令：
  - `python scripts/cli.py ingest-posts`
- `ingest-posts` 只负责：
  - 接收帖子详情 payload
  - 接收目标 `posts` 目录绝对路径
  - 使用已登录 Chrome/CDP 抓取图片
  - 写 `post.json`
  - 在存在 `raw_detail` 时写 `raw.json`
  - 写 `assets/`
- `ingest-posts` 的正式输入输出语义保持通用：
  - 输入 = `posts[] + --posts-dir`
  - 输出 = `--posts-dir/<post_id>/...` 下的标准帖子包
  - 不在 skill 本体中引入 `session`、`workspace`、`candidate` 或 `selected` 语义
- `ingest-posts` 不允许自行调用小红书搜索或详情获取逻辑
- 图片抓取使用 `xhs-skills` 内部 CDP 能力，以“导航到图片页 + 截取 `<img>` 元素”的方式保存
- 帖子目录按需惰性创建，不预先批量创建空目录
- 当前产品运行时创建 session 时，会预先创建：
  - `workspace/`
  - `workspace/posts/`
  作为 `017` 默认下载目标目录骨架
- 图片命名固定为：
  - `image-01.jpg`
  - `image-02.jpg`
  - 依此类推
- 首版严格只处理图文帖子：
  - 搜索阶段应显式带 `--note-type 图文`
  - 视频帖子不进入详情获取
  - 视频帖子不进入帖子包落盘结果
- 若单篇帖子失败，不终止整轮任务
- 若部分图片下载失败，仍允许保留该帖的详情对象

## 执行链路

### 1. 调研采集

- agent 读取 `xhs-explore`
- 执行搜索
- 搜索时显式限制 `--note-type 图文`
- 根据热度或搜索结果优先级，选取 Top 3 篇图文帖子
- 对这 3 篇图文帖子逐条执行详情获取
- 若结果中存在视频帖子，直接跳过，不回退补视频

### 2. 结构化交接

- agent 将 Top 3 篇图文帖子的结构化详情结果交给 `xhs-research-ingest`
- `xhs-research-ingest` 先使用 `write_file` 把 `posts[]` payload 写到一个临时 JSON 文件，再执行：
  - `python scripts/cli.py ingest-posts --posts-dir <target_posts_dir> --input-json <payload>`
- `write_file` 在该链路中允许直接接收 `dict/list` 形式的 JSON payload，并自动序列化成文件
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
    - 无则不阻止落盘，CLI 应优先使用显式结构化字段完成写入

### 3. 帖子包落盘

- `ingest-posts` 直接接收目标 `posts` 目录绝对路径
- 对每篇帖子惰性创建：
  - `<posts_dir>/<post_id>/`
  - `.../assets/`
- 使用浏览器截图方式保存图片到 `assets/`
- 写入：
  - `post.json`
  - `raw.json`（仅当 `raw_detail` 存在时）

### 4. 用户可见结果

- `run` 返回文本调研摘要
- 用户可基于已落地的帖子包在前端手动执行“加入已选”

## 内部组件

### xhs-explore

职责：

- 搜索小红书帖子
- 获取帖子详情
- 输出可用于后续下载的详情结果

不负责：

- 调研类工作流编排
- 帖子包目录创建
- 图片落盘
- `selected_posts.json` 写回

### runtime system prompt

职责：

- 规定调研类请求应使用 `xhs-explore`
- 规定调研类请求应从搜索结果中选取 Top 3 篇图文帖子
- 规定搜索时必须显式限制 `--note-type 图文`
- 规定视频帖子在首版直接跳过
- 规定详情获取后应调用 `xhs-research-ingest`
- 规定在当前产品运行时中，`xhs-research-ingest` 的 `--posts-dir` 默认指向当前 session 根目录下的 `workspace/posts`
- 规定 runtime context 中必须直接给出：
  - `Session Root Path`
  - `Workspace Data Root`
  让模型无需自行推导 `workspace/` 路径
- 规定后续若要基于下载结果生成总结、文案或图片，只能消费 `selected_posts.json` 对应帖子，不默认消费全部帖子包
- 规定最终输出必须包含文本调研摘要和本地帖子包结果

### xhs-research-ingest / ingest-posts

职责：

- 接收结构化帖子详情
- 接收目标 `posts` 目录
- 使用已登录 Chrome/CDP 抓取图片
- 写 `post.json`
- 在有 `raw_detail` 时写 `raw.json`
- 生成标准帖子包目录

不负责：

- 搜索帖子
- 获取帖子详情
- 更新 `selected_posts.json`
- 理解当前 topic/session/workspace 业务语义
- 生成总结对象

## 与现有 feature 的关系

- `015-agent-skills-loader`
  - 继续负责 skill 扫描与加载
- `016-agent-local-harness`
  - 可作为本地 smoke 入口验证 `017`
- `021-topic-truth-store`
  - 继续定义 `post.json`、`raw.json`、`assets/` 的帖子结构边界
- `017` 不负责自动更新 `selected_posts`
- `017` 只保证把帖子下载成标准帖子包；进入后续流程时，是否被消费由 `selected_posts.json` 决定

## 验收标准

- 一次调研请求后，agent 会自动处理 Top 3 篇图文帖子
- 本轮会返回一段文本调研摘要
- 目标 `posts` 目录中会新增或更新 3 个图文帖子包
- 每篇帖子会稳定写入：
  - `post.json`
  - `assets/`
- 若提供了 `raw_detail`，则额外写入 `raw.json`
- 本轮不会自动更新 `selected_posts.json`
