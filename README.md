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

- 前端三栏工作台原型
- 话题工作区、候选帖子区、内容创作区、对话主栏的基础交互
- Tailwind + 自定义轻量组件 + Lucide + Framer Motion 的前端表达
- 前端单测、E2E 和构建验证
- Python Agent Runtime 首版
- session/history 子系统
- context memory 与 memory consolidator
- loop、tools、skills loader、local harness
- 本地 trace 联调能力
- FastAPI 最小后端胶水层
- `topic_id -> active_session_id` 文件映射
- 前端主栏与后端真实 API 打通
- session workspace 数据层
- topic 列表、创建、删除与真实路由
- 右侧 `candidatePosts` / `patternSummary` 与后端真实数据打通
- 候选帖子详情多图翻页

当前还没有正式落地：

- 更完整的右侧工作区真实化
- 面向产品体验的流式输出
- 更深入的 xhs 任务执行链路

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

- topic 元数据与 active session 映射落在 `data/topics/`
- session 历史、memory 与 workspace 数据落在 `data/sessions/`
- 目录下按对象拆分小文件

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
- [x] 右侧工作区与后端对接：`candidatePosts` / `patternSummary` 已接通
- [ ] 前端首页 / 入口体验重做
- [ ] 流式输出
- [ ] 提示词调优，路径约束单独一部分，角色定义
- [ ] 真实 xhs 任务与 agent 联调：发散搜索、帖子阅读、帖子下载
- [ ] 右侧其余 workspace section 继续去 mock 化

## 说明

这个 README 主要用于介绍项目本身、当前状态和开发入口。

更细的功能边界、交互规则和验收标准，请直接查看 `specs/`。
