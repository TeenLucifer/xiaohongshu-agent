# 021 Session Workspace Store

## 背景

`020-backend-glue-minimal` 只解决了前端主栏与 agent runtime 的最小联调，并没有让右侧 workspace 相关业务对象形成稳定的数据层。候选帖子、已选帖子、模式总结、文案和图片结果仍然需要独立边界，但这些对象现在被明确视为当前 active session 的 workspace 产物，而不是跨 session 复用的 topic 真相层。

## 目标

- 固定 session workspace 数据层的文件化目录结构
- 固定右侧 workspace 业务对象的最小 schema
- 固定后端对 workspace 真相对象的读写边界
- 为后续右侧工作区替换 mock 提供稳定数据来源
- 第一波打通 `candidatePosts`、`patternSummary` 与 `copyDraft` 的真实读取链路
- 候选帖子详情支持为后续多图浏览提供稳定图片数组
- 固定“全部帖子包 + 已选列表”的分层关系

## 非目标

- agent runtime 本身的 session/history/memory
- 流式输出
- 数据库
- 搜索索引
- 复杂任务编排
- `imageResults`、`materials`、`collector` 的本轮真实化
- 候选帖子选择/排序写回
- 文案编辑写回

## 用户故事

- 作为后端实现者，我希望右侧 workspace 相关业务对象有独立文件真相层，而不是散落在 session 或前端 mock 中。
- 作为前端接入方，我希望右侧工作区最终能读取稳定的 workspace 对象，而不是直接依赖运行时内部结构。

## 输入输出

- 输入：
  - `topic_id`
  - topic 元数据
  - 全部帖子包、已选帖子、总结、文案、图片等对象
- 输出：
  - 稳定的 session workspace 文件目录
  - 稳定的 workspace 对象 schema
  - 面向前端的 workspace DTO

## 约束

- `020` 继续以 `data/topic-index.json` 中的 `topic_id -> session_id` 作为前端入口映射
- `021` 的数据根目录跟随当前 active session，位于 `data/sessions/<session_id>/workspace/`
- workspace 数据层不再独立落在 `data/topics/<topic_id>/`
- 当前 session 目录中的 `topic.json` 保存该 workspace 所属 topic 的标题与描述
- workspace 数据层与 session 历史/记忆分层：
  - session 历史、memory 继续归 `011/012`
  - session workspace 对象归 `021`
- session workspace 数据层采用文件化存储
- 第一版不引入数据库
- 后端通过单独的 workspace store 读写当前 session 的 workspace 数据层
- session workspace 数据层必须可被后续前端右侧 workspace 稳定消费
- session workspace 数据层不直接替代 `AgentRuntime` 的会话历史
- `021` 只定义对象如何存储，不定义帖子如何被读取或下载
- 正式 schema 使用英文键
- 原始抓取对象仅保留在 `raw.json`
- 帖子图片/资源复制进当前 session 的 workspace 目录，不只保存外部引用
- 搜索结果真相来自当前 workspace 下的全部帖子包，不单独维护 `candidate_posts.json`
- `selected_posts.json` 只保存用户手动选择和顺序，不冗余帖子详情字段
- 第一波真实化覆盖：
  - `candidatePosts`
  - `patternSummary`
  - `copyDraft`
- 第一波右侧读取链路以只读为主，但 `selected_posts.json` 已支持最小写回交互
- 进入后续总结、文案、图片等流程时，默认只消费 `selected_posts.json` 对应帖子，不直接消费全部帖子包
- 右侧 section 标题、状态与 summary 第一波继续沿用前端 mock
- 列表卡片继续只使用单张封面图
- 帖子详情可额外读取并暴露全部图片数组，用于弹窗内逐张浏览

## 目录结构

建议目录规则：

- `data/sessions/<session_id>/workspace/meta.json`
- `data/sessions/<session_id>/workspace/selected_posts.json`
- `data/sessions/<session_id>/workspace/pattern_summary.json`
- `data/sessions/<session_id>/workspace/copy_draft.json`
- `data/sessions/<session_id>/workspace/image_results.json`
- `data/sessions/<session_id>/workspace/posts/<post_id>/post.json`
- `data/sessions/<session_id>/workspace/posts/<post_id>/raw.json`
- `data/sessions/<session_id>/workspace/posts/<post_id>/assets/...`

首版允许按实现需要微调文件名，但必须满足：

- 一个 active session 一套 workspace 目录
- session workspace 元数据与业务对象分文件存储
- 文件结构稳定、可读、可测试
- 帖子 detail/raw/assets 只作为 workspace 对象的底层支撑，不承担执行流程语义

## 最小对象边界

### Topic Meta

- `topic_id`
- `title`
- 可选 `description`
- `updated_at`

说明：

- `Topic Meta` 保存于 `data/sessions/<session_id>/topic.json`
- 不再单独放在 `data/topics/<topic_id>/`

### Selected Posts

- 已选帖子列表
- 每条只包含：
  - `post_id`
  - `manual_order`
- 不冗余标题、作者、封面、正文等帖子详情字段

### Pattern Summary

- 面向工作区展示的结构化总结对象：
  - `title_patterns`
  - `body_patterns`
  - `keywords`
  - 可选 `summary_text`
  - 可选 `source_post_ids`

### Copy Draft

- 内容创作阶段的结构化文案对象

### Image Results

- 图片结果对象或图片产物索引

### Post Detail

- 单篇帖子详情对象，位于 `posts/<post_id>/post.json`
- 至少包含：
  - `post_id`
  - `title`
  - `post_type`
  - `url`
  - 可选 `published_at`
  - 可选 `author`
  - `content`
  - `metrics`
  - `media`
  - `updated_at`
- `media` 中的图片顺序需要稳定，供前端详情弹窗按顺序翻页

### Raw Post

- 原始抓取对象，位于 `posts/<post_id>/raw.json`
- 仅用于追溯与二次解析，不直接作为前端消费对象

### Post Assets

- 帖子资源文件，位于 `posts/<post_id>/assets/`
- 第一版以图片资源为主
- 资源文件复制进当前 session workspace 目录，供 workspace 稳定引用

## 内部组件

### SessionWorkspaceStore

职责：

- 管理 session workspace 目录与文件存在性
- 读写 workspace 元数据与业务对象
- 提供最小容错读取

不负责：

- 调用 runtime 执行 agent
- 流式传输
- topic/session 映射
- 帖子读取、下载、抓取执行流程

### Workspace Context DTO

职责：

- 从 `SessionWorkspaceStore` 读取右侧 workspace 需要的对象
- 组装前端可直接消费的最小只读 DTO
- 第一波暴露：
  - `candidate_posts`
  - `pattern_summary`
  - `copy_draft`
- `candidate_posts` 在只读 DTO 中由：
  - `posts/<post_id>/post.json`
  - `selected_posts.json`
  共同组装
- `candidate_posts` 在只读 DTO 中保留单封面 `imageUrl`
- 候选帖详情可附带完整 `images[]`，用于多图帖子详情翻页

不负责：

- 主栏对话 DTO
- 右侧写回接口
- 其余 section 的真实化

## 与 `020` 的关系

- `021` 依赖 `020` 已存在的后端服务入口
- `020` 的主栏 API 可先不依赖 `021`
- 后续右侧 workspace 真实化时，由后端在 `020` 的服务层中先 resolve 当前 active session，再组合 `021` 的 session workspace 数据
- `021` 不负责定义帖子 ingestion 或 skill 执行流程，这类执行语义留到 agent 层后续讨论
- 第一波通过单独的右侧 `context` 读取接口暴露数据，不扩展 `020` 现有主栏 `GET /workspace`

## 第一波接入范围

- 接入真实数据：
  - `candidatePosts`
  - `patternSummary`
  - `copyDraft`
- 继续保留 mock：
  - `materials`
  - `collector`
  - `imageResults`

## 读取接口与 DTO

第一波后端新增单独读取接口：

- `GET /api/topics/{topic_id}/context`

返回最小 `WorkspaceContextResponse`：

- `topic_id`
- `topic_title`
- `candidate_posts`
- `pattern_summary`
- `copy_draft`
- `updated_at`

DTO 策略：

- 尽量贴近现有前端类型
- `candidate_posts` 贴近前端 `CandidatePost[]`
- `pattern_summary` 贴近前端 `PatternSummaryContent`
- `copy_draft` 贴近前端 `CopyDraftContent`

转换约束：

- `CandidatePost.id` 直接使用 `post_id`
- `bodyText` 从 `posts/<post_id>/post.json.content.text` 读取
- `imageUrl` 从 `posts/<post_id>/post.json.media[0]` 或首张可用图片资源推导
- `images[]` 由 `posts/<post_id>/post.json.media[]` 顺序映射
  - 每项至少包含稳定 `id`、可访问 `imageUrl` 和基础 `alt`
  - 若 `media[]` 为空，则允许回退为仅包含封面图的单项数组
- `selected` 与 `manualOrder` 由 `selected_posts.json` 映射
- session workspace 内部资源图片通过后端资源读取路径暴露给前端
  - 例如：`/api/topics/{topic_id}/assets/...`
- `heat` 由 `likes/favorites/comments` 组装为前端当前展示字符串

## 验收标准

- 当前 active session 对应的 workspace 目录结构稳定
- workspace 元数据与业务对象 schema 稳定
- 已选帖子、总结、文案、图片结果能各自独立读写
- 单篇帖子 detail/raw/assets 可作为候选帖子详情支撑对象独立读写
- session workspace 数据层与 session 历史/记忆边界清晰
- 右侧工作区后续可基于该 session workspace 数据层替换当前 mock 数据
- 第一波要求 `candidatePosts`、`patternSummary` 与 `copyDraft` 可被后端读取并返回给前端
- `candidatePosts` 由全部帖子包和 `selected_posts.json` 组装，而不是依赖独立候选文件
- 多图帖子在候选帖详情场景下可基于 `media[]` 暴露完整图片数组
