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

当前已经完成的主要部分是前端原型：

- 三栏工作台
- 候选帖子区
- 内容创作展示区
- 聊天式主栏

当前还没有正式落地的部分：

- Agent Runtime
- Skill 协议
- 后端胶水层
- 文件化持久层

所以后续如果进入 agent / 后端阶段，应新增新的 feature 编号，不继续把任务堆进 `001~004`。

## 新 Feature 约定

新增能力时，优先按“能力边界”开 spec，不按技术层随意拆。

建议做法：

- 前端交互改动：继续在前端相关 feature 下演进
- Agent Runtime：单独开新 feature
- Skill 协议：单独开新 feature
- 文件化存储：单独开新 feature
- 前后端联调：单独开 integration feature

## 文档边界

- `AGENTS.md`
  - 只放协作规则和 specs 导航
- `README.md`
  - 只放项目介绍、当前状态和启动方式
- `specs/`
  - 放功能设计、任务拆分和验收标准
- `docs/`
  - 放架构说明、术语表和技术决策

## 默认工程要求

- 代码改动不能绕开 spec
- 不要跨层直接耦合内部实现
- 不要在模块间传递不透明裸数据
- 不要顺手扩展 spec 之外的能力
- 不要把临时调试代码留在正式路径

## 备注

如果 `AGENTS.md`、`README.md` 与 `specs/` 出现冲突，默认以 `specs/` 为准。
