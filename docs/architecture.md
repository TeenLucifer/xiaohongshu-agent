# 架构概览

## 当前架构目标

本项目当前采用“前端工作台 + 主 agent runtime + 后续 backend glue”的单仓结构。

目标不是先做一个通用聊天机器人，而是先把面向运营工作流的核心链路拆清楚：

- 前端负责人工交互与结果展示
- agent runtime 负责 session 级执行
- 后端后续负责真相层与编排胶水

## 当前分层

### 1. 前端工作台

位于 `web/`，负责：

- 话题工作台 UI
- 候选帖子管理
- 内容结果展示
- 对话式主栏交互

### 2. Agent Runtime Foundation

由 `010-agent-runtime-foundation` 定义，是一个薄宿主层，内部协调：

- `SessionManager`
- `ContextBuilder`
- `SkillsLoader`
- `ToolsRegistry`
- `LoopRunner`

runtime 只认 `session_id`，不直接以业务 `topic` 作为执行主键。

### 3. Session / History

由 `011-session-history-core` 定义，负责：

- `Session`
- `SessionSnapshot`
- `SessionManager`
- 短期历史
- `jsonl` 持久化
- `last_consolidated`

### 4. Context / Memory

由 `012-context-memory-core` 定义，负责：

- 长期记忆
- 上下文窗口治理
- consolidation
- `MEMORY.md`
- `HISTORY.md`

### 5. Loop Runner

由 `013-agent-loop-runner` 定义，负责：

- tool-calling loop
- tool 回灌
- 停止条件
- memory hook
- 最终结果汇总

### 6. Tools

由 `014-agent-tools-core` 定义，首版只包含：

- 文件系统工具
- `exec`

### 7. Skills Loader

由 `015-agent-skills-loader` 定义，采用 nanobot 风格：

- 扫描 `SKILL.md`
- summary
- `always skills`
- requirement 检查

### 8. Local Harness

由 `016-agent-local-harness` 定义，作为本地 smoke 验证入口：

- Python 主入口
- 薄 CLI

### 9. Backend Glue

后续新增 feature 负责：

- 文件化真相层
- 前后端编排
- runtime 调用与结果回写

## 数据与控制流

当前设计下的主链路是：

1. 前端围绕话题组织工作区和用户操作
2. 后端后续把话题映射到一个或多个 session
3. runtime 通过 `session_id` 获取会话
4. `ContextBuilder` 组装：
   - identity
   - bootstrap
   - memory
   - always skills
   - skills summary
   - session history
   - current user message
5. `LoopRunner` 调模型、调 tools、回灌结果
6. `SessionManager` 持久化短期历史
7. `Context Memory` 在需要时沉淀长期记忆

## 设计原则

- 产品层围绕 `topic`，runtime 层围绕 `session`
- 一个主 agent runtime，不做多个对等 agent
- skill 协议尽量贴 nanobot，不另起新协议
- tools 保持极简，浏览器能力不内置
- docs 表达稳定结论，详细边界以 `specs/` 为准
