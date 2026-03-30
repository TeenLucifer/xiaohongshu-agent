# 项目协作与 Specs 导航

始终使用中文简体回复。

## 这个文档的作用

`AGENTS.md` 不是详细设计文档，也不是功能说明文档。  
它只负责两件事：

- 说明这个仓库的协作方式
- 作为 `specs/` 的导航入口

具体功能边界、任务拆分、验收标准，一律以下面这些文档为准：

- `specs/<feature>/spec.md`
- `specs/<feature>/tasks.md`
- `specs/<feature>/acceptance.md`

## 协作规则

- 所有功能开发默认走 `SDD + TDD`
- 开始实现前，必须先读：
  - 根目录 `AGENTS.md`
  - 对应 feature 的 `spec.md`
  - 对应 feature 的 `tasks.md`
- 如果需求还没有对应 spec，先补 spec，再开始实现
- 完成后必须同步更新：
  - `tasks.md`
  - `acceptance.md`
- 不要让 `tasks.md` 变成历史流水账
  - `spec.md` 表达当前真相
  - `tasks.md` 表达当前阶段任务
  - 历史过程交给 `git`

## 当前 Specs 导航

### 基础

- `000-foundation`
  - 基础工程骨架、配置、日志、异常、测试基线

### 前端工作台

- `005-home-entry`
  - 首页“新话题”入口、历史话题次入口与左侧“新话题”导航
- `006-skills-page`
  - Skills 独立页、skills 列表与技能详情弹窗
- `001-topic-workspace`
  - 话题工作台整体结构
  - 左侧导航、中间对话主栏、右侧工作区
- `002-candidate-posts`
  - 候选帖子展示、选择、排序、详情弹窗
- `003-content-creation`
  - 总结、文案、图片结果在前端的展示方式
- `004-conversation-timeline`
  - 中间主栏的聊天化消息流

## 当前仓库状态

当前主分支已经完成的主要部分：

- “新话题”首页入口与历史话题次入口
- 前端三栏工作台
- Skills 独立页与技能详情弹窗
- 话题列表、创建/删除与真实 topic 管理
- 聊天式主栏与真实后端 run API
- Agent Runtime 首版
- Session / History 子系统
- Context Memory 子系统
- 后端最小胶水层
- session workspace 数据层
- 候选帖子与总结的右侧工作区真实化

当前仍在继续推进的部分：

- 更完整的右侧工作区真实化
- 流式输出
- 更深入的 xhs 任务执行能力

所以后续如果进入 agent / 后端阶段，应继续沿 `010+` 和 `020+` 的编号推进，不再把任务堆进 `001~004`。

## 新 Feature 约定

新增能力时，优先按“能力边界”开 spec，不按技术层随意拆。

建议做法：

- 前端交互改动：继续在前端相关 feature 下演进
- Agent Runtime：单独开新 feature
- Skill 协议：单独开新 feature
- 文件化存储：单独开新 feature
- 前后端联调：单独开 integration feature

### Agent Runtime

- `010-agent-runtime-foundation`
  - 主 runtime 薄宿主层、公开接口、ContextBuilder 基础骨架
- `011-session-history-core`
  - Session、SessionManager、短期历史与持久化
- `012-context-memory-core`
  - 长期记忆、上下文窗口治理与记忆注入
- `013-agent-loop-runner`
  - tool-calling loop、本轮执行与停止逻辑
- `014-agent-tools-core`
  - 默认文件系统与 shell 工具层
- `015-agent-skills-loader`
  - nanobot 风格 skills 扫描与加载
- `016-agent-local-harness`
  - 本地 Python 调用入口与 smoke harness
- `017-xhs-research-persist-loop`
  - 小红书调研闭环、Top 6 帖子详情采集、图片下载与 session workspace 落盘

### 后端与集成

- `020-backend-glue-minimal`
  - 最小后端胶水层、`data/topic-index.json` 映射与同步主栏 API
- `021-topic-truth-store`
  - session workspace 数据层、候选帖子/总结/文案/图片等右侧工作区对象存储
- `022-streaming-run-api`
  - 基于后端 run 接口的流式输出协议与主栏渐进展示能力
- `023-topic-management`
  - topic 列表、创建/删除、`topic_id` 生成与 active session 建立

## 文档边界

- `AGENTS.md`
  - 只放协作规则和 specs 导航
- `README.md`
  - 只放项目介绍、当前状态和启动方式
- `specs/`
  - 放功能设计、任务拆分和验收标准
- `docs/`
  - 放架构说明、术语表和技术决策
- `功能.md`
  - 放项目能力概览，不替代 `specs/`

## 默认工程要求

- 代码改动不能绕开 spec
- 不要跨层直接耦合内部实现
- 不要在模块间传递不透明裸数据
- 不要顺手扩展 spec 之外的能力
- 不要把临时调试代码留在正式路径

## 备注

如果 `AGENTS.md`、`README.md`、`功能.md` 与 `specs/` 出现冲突，默认以 `specs/` 为准。
