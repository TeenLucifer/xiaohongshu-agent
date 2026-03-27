# 术语表

- `Feature`
  - 一个独立推进的能力单元，对应 `specs/<feature>/`

- `spec.md`
  - 定义需求、边界和稳定约束

- `tasks.md`
  - 定义实施顺序、测试项和实现任务

- `acceptance.md`
  - 定义手工与自动化验收路径

- `Session`
  - runtime 的真正工作单元，持有短期历史、工作目录和基础 metadata

- `SessionSnapshot`
  - 面向外部暴露的轻量会话快照，不等同于内部 `Session` 实体

- `SessionManager`
  - 负责 session 的创建、加载、保存、缓存和失效

- `ContextBuilder`
  - 负责组装 system prompt、长期记忆、skills summary、session history 和当前 user message

- `LoopRunner`
  - 负责一次 run 的 tool-calling loop，包括模型调用、tool 执行和结果回灌

- `ToolsRegistry`
  - 负责注册和暴露 runtime 默认工具

- `SkillsLoader`
  - 负责扫描、解析和加载 nanobot 风格 skills

- `always skills`
  - 被标记为 `always=true` 且依赖满足的 skills，会在 system prompt 中常驻注入

- `Session History`
  - 短期记忆部分，来自 `Session.get_history(...)`

- `last_consolidated`
  - session 上的游标，表示已成功沉淀进长期记忆的历史边界下标

- `MEMORY.md`
  - session 级长期记忆文件，保存完整更新版长期记忆

- `HISTORY.md`
  - session 级历史归档文件，保存追加写入的 consolidation 记录

- `Local Harness`
  - 本地试跑与 smoke 验证入口，用于在后端接入前验证 runtime 是否能工作

- `Skills Summary`
  - 注入到 prompt 中的 skill 元数据摘要，告诉模型当前有哪些 skill 可用

- `schema`
  - 跨层输入输出的结构化类型定义

- `adapter`
  - 用于隔离外部系统、模型接口或持久化实现的边界层
