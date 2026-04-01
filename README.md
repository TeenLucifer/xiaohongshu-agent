# 小红书运营 Agent 工作台

一个面向小红书运营场景的 Agent 项目。

它的目标不是做通用聊天机器人，而是围绕一个明确的话题工作区，把素材整理、帖子搜集、内容总结、文案创作和图片创作串成一条可控的创作链路。

当前仓库处于可联调阶段：前端工作台原型已经完成，agent 侧 `010~016` specs 与对应代码实现已经落地，`020~023` 的后端、session workspace、topic 管理也已经有首版实现，前端主栏与部分右侧工作区已经可以通过真实后端 API 读取数据。

## 项目定位

这个项目聚焦三个方向：

- 以“话题”作为产品层工作单元，沉淀一次运营任务的全部上下文
- 以“一个主 Agent + 多个 Skills”的方式组织能力，而不是堆多个对等 Agent
- 以前端工作台承载人工决策，以后端持久化和编排能力承载系统真相

当前已经明确的产品形态是：

- 产品围绕话题组织工作区
- runtime 围绕 session 执行与复用上下文
- 帖子搜集、模式总结、文案创作、图片创作作为 skills 挂在同一个主 agent 下
- session/history、memory、loop、tools、skills loader、local harness 已经拆成独立 specs 并完成首版实现

## 当前状态

目前主分支已经完成：

- “新话题”首页入口与历史话题次入口
- 前端三栏工作台原型
- Skills 独立页与技能详情弹窗
- 话题工作区、候选帖子区、内容创作区、对话主栏的基础交互
- Tailwind + 自定义轻量组件 + Lucide + Framer Motion 的前端表达
- 前端单测、E2E 和构建验证
- Python Agent Runtime 首版
- session/history 子系统
- context memory 与 memory consolidator
- loop、tools、skills loader、local harness
- 本地 trace 联调能力
- FastAPI 最小后端胶水层
- `data/topic-index.json` 话题到 session 的轻量映射
- 前端主栏与后端真实 API 打通
- 主栏只展示 final answer，并附折叠 tool 摘要
- 聊天消息与 Skills 详情支持 Markdown 显示
- 基于 SSE 的主栏流式输出首版
- 右侧文案区采用白板式 Markdown 富文本编辑，并真实写回 `copy_draft.json`
- session workspace 数据层
- topic 列表、创建、删除与真实路由
- 右侧 `candidatePosts` / `patternSummary` 与后端真实数据打通
- 候选帖子详情多图翻页
- xhs 图文帖子搜索、详情获取与标准帖子包下载链路
- `xhs-research-ingest` 通用帖子下载 skill
- `image-analysis` 帖子图片视觉分析 skill（硅基流动视觉 API）
- 总结时支持图片分析，前端展示图片模式
- 开发态 web trace 与宿主机浏览器联调路径
- 真实图片生成链路与右侧图片结果区打通

当前还没有正式落地：

- 更完整的右侧工作区真实化
- 更细的编辑体验打磨与提示词调优

也就是说，这个仓库现在更像一个“已可前后端联调的 Agent 工作台”，但仍然不是一个已经完工的全栈产品。

## 核心思路

项目在产品层围绕“话题”组织入口和路由，在 runtime 层围绕 `session` 执行与持久化 workspace 数据。

每个话题后续会沉淀：

- 话题元数据
- 用户素材
- 候选帖子
- 已选帖子与排序
- 模式总结
- 文案草稿
- 图片结果
- Agent 会话记录
- Skill 运行记录

当前后端已经采用“纯文件化”作为主要真相层：

- `data/topic-index.json` 保存 `topic_id -> session_id` 轻量索引
- topic 元数据、session 历史、memory 与 workspace 数据落在 `data/sessions/<session_id>/`
- 目录下按对象拆分小文件
- session 创建时会预建 `workspace/` 与 `workspace/posts/`
- runtime context 会显式提供：
  - `Session Root Path`
  - `Workspace Data Root`

## 技术方向

当前已落地：

- 前端：React + Vite
- 样式：Tailwind CSS
- 动效：Framer Motion
- 图标：Lucide
- 测试：Vitest + Playwright

当前约定并已部分落地：

- 后端 / Agent：Python 3.11+
- 依赖与命令：uv
- 质量门禁：ruff、pyright、pytest

## 仓库结构

```text
specs/     功能规格、任务拆分与验收标准
web/       前端工作台原型
src/       Agent runtime、memory、tools、skills、local harness 等代码
skills/    builtin skills
scripts/   辅助脚本与同步脚本
docs/      架构、术语和技术决策
```

其中：

- `specs/001~004` 当前对应前端工作台相关能力
- `specs/010~016` 当前对应 agent runtime 相关能力
- `specs/020~023` 当前对应后端胶水、session workspace、流式 run API、topic 管理

## 快速开始

当前仓库可直接运行的是：

- 前端工作台
- 最小后端 API
- 本地 agent harness

```bash
cd web
npm install
npm run dev
```

启动最小后端：

```bash
PYTHONPATH=src .venv/bin/python -m backend.app
```

如果你希望前端显式指向本地后端：

```bash
cd web
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

如果不显式传入，前端默认会回退到：

```text
http://127.0.0.1:8000
```

常用命令：

```bash
cd web
npm test
npm run test:e2e
npm run build
```

本地 agent 联调示例：

```bash
PYTHONPATH=src .venv/bin/python -m agent.local_harness run \
  --topic "联调测试" \
  --user-input "smoke run" \
  --trace
```

后端 API 联调示例：

```bash
curl "http://127.0.0.1:8000/api/topics/topic-demo/workspace?topic_title=%E8%AF%9D%E9%A2%98%E6%BC%94%E7%A4%BA"

curl -X POST "http://127.0.0.1:8000/api/topics/topic-demo/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_title": "话题演示",
    "user_input": "帮我总结一下这个话题的切入方向"
  }'
```

## 开发方式

这个仓库默认按 `SDD + TDD` 推进：

- 先写 `spec.md`
- 再写 `tasks.md`
- 再写 `acceptance.md`
- 最后实现和测试

更具体的工程规则见：

- [AGENTS.md](/home/t-rex/projects/xiaohongshu-agent/AGENTS.md)
- [架构概览](/home/t-rex/projects/xiaohongshu-agent/docs/architecture.md)
- [技术决策](/home/t-rex/projects/xiaohongshu-agent/docs/tech-decisions.md)

## TODO

- [x] 真实 xhs 任务与 agent 联调：搜索任务能实现
- [x] 后端：020 最小胶水层已落地
- [x] 与前端对接：主栏已接通真实后端 API
- [x] Topic 管理：列表、创建、删除已落地
- [x] 前端”新话题”首页入口已落地
- [x] 前端 Skills 页面已落地
- [x] 右侧工作区与后端对接：`candidatePosts` / `patternSummary` 已接通
- [x] 真实 xhs 任务与 agent 联调：图文帖子搜索、详情获取、标准帖子包下载（`017`）
- [x] 支持 md 格式展示：聊天消息、skill显示
- [x] 流式输出
- [x] 帖子图片视觉分析 skill（`024`）
- [x] 总结时支持图片分析，前端展示图片模式
- [x] 文案改写、图片生成的真实结果链路
- [x] 右侧文案白板式 Markdown 编辑与真实写回
- [ ] 前端”设置”页面实现
- [x] 前端工作区折叠弹出无动画 bug
- [x] 前端对话有空消息 bug
- [x] 帖子显示调优，图片框框大小固定
- [ ] 提示词调优，路径约束单独一部分，角色定义
- [ ] 前端”新话题”页面视觉调优
- [x] 前端对话调优，工具结果可以显示摘要
- [ ] skill 部分spec收成同一个
- [ ] 相同图片拖入编辑区bug
- [ ] 各skill的api都收到自己内部
- [ ] 提示词形式搞成静态+注入
- [ ] 文案编辑可自选区域AI润色
- [ ] 对话界面作为工作区的一个tab，工作区每块区域加对话框
- [ ] 总结作为搜索结果的下面一部分，不作为单独的section，在搜索完成后自动触发，也可手动选贴后手动触发
- [ ] 各section不需要显示已就绪
- [ ] 把一些没用的辅助文字删了

## 说明

这个 README 主要用于介绍项目本身、当前状态和开发入口。

更细的功能边界、交互规则和验收标准，请直接查看 `specs/`。
