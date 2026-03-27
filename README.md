# 小红书运营 Agent 工作台

一个面向小红书运营场景的 Agent 项目。

它的目标不是做通用聊天机器人，而是围绕一个明确的话题工作区，把素材整理、帖子搜集、内容总结、文案创作和图片创作串成一条可控的创作链路。

当前仓库处于早期阶段：前端工作台原型已经完成，Agent Runtime 和后端胶水层正在设计中。

## 项目定位

这个项目聚焦三个方向：

- 以“话题”作为工作单元，沉淀一次运营任务的全部上下文
- 以“一个主 Agent + 多个 Skills”的方式组织能力，而不是堆多个对等 Agent
- 以前端工作台承载人工决策，以后端持久化和编排能力承载系统真相

当前已经明确的产品形态是：

- 一个话题对应一个长期会话
- 帖子搜集是主 Agent 的核心能力
- 模式总结、文案创作、图片创作作为 Skills 挂在同一个 Agent 下
- 每一步由前端或后端显式指定当前 skill 执行

## 当前状态

目前主分支已经完成：

- 前端三栏工作台原型
- 话题工作区、候选帖子区、内容创作区、对话主栏的基础交互
- Tailwind + 自定义轻量组件 + Lucide + Framer Motion 的前端表达
- 前端单测、E2E 和构建验证

当前还没有正式落地：

- Python Agent Runtime
- 后端编排与文件化持久层
- 浏览器自动化搜集链路
- Skills 安装与执行协议

也就是说，这个仓库现在更像一个“前端原型 + 后端/Agent 设计中的单仓工程”，而不是一个已经完工的全栈产品。

## 核心思路

项目围绕“话题”组织数据和流程。

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

首版后端会以“纯文件化”作为真相层：

- 每个话题一个目录
- 目录下按对象拆分小文件
- Agent 工作目录只是执行上下文，不是系统最终真相

## 技术方向

当前已落地：

- 前端：React + Vite
- 样式：Tailwind CSS
- 动效：Framer Motion
- 图标：Lucide
- 测试：Vitest + Playwright

当前约定但尚未落地：

- 后端 / Agent：Python 3.11+
- 依赖与命令：uv
- 质量门禁：ruff、pyright、pytest

## 仓库结构

```text
specs/   功能规格、任务拆分与验收标准
web/     前端工作台原型
src/     后端与 Agent 代码入口，当前尚未展开
docs/    架构、术语和技术决策
```

其中：

- `specs/001~004` 当前对应前端工作台相关能力
- 后续 Agent 与后端会进入新的 feature 编号，而不是继续堆到前端 spec 里

## 快速开始

当前仓库可直接运行的是前端原型。

```bash
cd web
npm install
npm run dev
```

常用命令：

```bash
cd web
npm test
npm run test:e2e
npm run build
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

## 下一阶段

接下来的工作重点是：

- 设计并实现主 Agent Runtime
- 定义 Skill 协议
- 建立话题级纯文件化持久层
- 增加后端胶水层，把前端工作台和 Agent 执行链路接起来

## 说明

这个 README 主要用于介绍项目本身、当前状态和开发入口。

更细的功能边界、交互规则和验收标准，请直接查看 `specs/`。
