# 010 Agent Runtime Foundation

## 背景

前端工作台已经基本稳定，下一阶段需要先建立主 agent 的基础运行宿主层，为后续 tools、skills、loop 和本地 harness 提供稳定边界。

本 feature 参考 `nanobot` 的总体形态，但不照搬其聊天渠道模型。本项目的 runtime 以 `Session` 为真正工作单元，`topic` 只是 session metadata。

## 目标

- 建立一个薄的 `AgentRuntime` 宿主层
- 固定内部 5 个组件边界：
  - `SessionManager`
  - `ContextBuilder`
  - `SkillsLoader`
  - `ToolsRegistry`
  - `LoopRunner`
- 固定 `Session` 数据边界
- 固定 `ContextBuilder` 的系统提示词与消息组装顺序
- 固定 runtime 对外最小接口和输入输出模型
- 固定与 `nanobot` 一致的容错风格和最小错误边界

## 非目标

- `Session` / `SessionManager` 的详细协议
- 长期记忆与上下文窗口治理
- tools 具体实现
- skills 扫描细节与安装流程
- tool-calling loop 具体迭代逻辑
- 后端 API
- GitHub skill 安装
- run-level timeout
- 结构化 run 状态模型

## 用户故事

- 作为实现者，我希望先有一个薄的 runtime 宿主层，而不是一开始把 tools、skills 和 loop 堆进一个巨型类。
- 作为后续实现者，我希望 runtime 只认 `session_id`，避免与前端或后端的业务对象强耦合。
- 作为后续实现者，我希望 `ContextBuilder` 的基础拼接顺序先定死，后续实现不需要再猜。

## 运行宿主边界

### AgentRuntime

`AgentRuntime` 是薄宿主层，只负责协调，不承载具体实现细节。内部固定持有：

- `SessionManager`
- `ContextBuilder`
- `SkillsLoader`
- `ToolsRegistry`
- `LoopRunner`

`AgentRuntime` 负责：

- 创建和重置 session
- 基于 `session_id` 运行一次 agent 调用
- 读取 session 快照
- 串联 session、context、skills、tools、loop

`AgentRuntime` 不负责：

- tools 具体实现
- skills 协议设计
- loop 内部迭代逻辑
- Session/history 详细协议
- 长期记忆与上下文窗口治理
- 浏览器/CDP 能力
- 后端真相层与 API

## Session 与记忆边界

- runtime 主工作单元是 `Session`
- `topic` 只是 session metadata，不是主键
- `Session`、`SessionSnapshot`、`SessionManager`、短期历史与持久化细节见 `011-session-history-core`
- 长期记忆、上下文窗口治理与记忆注入细节见 `012-context-memory-core`

## ContextBuilder 组装顺序

### build_system_prompt()

固定顺序：

1. `identity + runtime rules`
2. `bootstrap files`
3. `memory`
4. `always skills`
5. `skills summary`

### bootstrap files

固定四件套，顺序固定为：

1. `AGENTS.md`
2. `SOUL.md`
3. `USER.md`
4. `TOOLS.md`

规则：

- 文件存在则拼入 system prompt
- 文件缺失直接跳过
- 缺失不报错

### memory / always skills / skills summary

memory 规则：

- 长期记忆来自 `012-context-memory-core`
- 以独立 memory section 注入 system prompt

always skills 规则：

- `always skills` 来自 `015-agent-skills-loader`
- 在 memory 之后、skills summary 之前注入
- 只注入依赖满足且被标记为 `always=true` 的 skills 正文

### skills summary

来源固定为：

- builtin skills
- 当前 workspace skills

作用：

- 注入所有可用 skills 的 metadata summary
- 提醒模型如需使用某个 skill，应先读取对应 `SKILL.md`

### build_messages()

固定顺序：

1. `system message`
2. `session history`
3. `current user message`

约束：

- `session history` 的具体来源由 `011-session-history-core` 定义
- runtime 不在 `010` 中重复定义 `get_history(...)` 细节

当前 user message 内部顺序固定为：

1. `runtime context`
2. `user_input`
3. `attachments`

### runtime context

首版固定只放：

- `Current Time`
- `Session ID`

并明确标记为：

- metadata only
- not instructions

### attachments

首版只注入附件路径引用，不内联文件内容。

## Runtime 对外接口

`AgentRuntime` 对外只公开 4 个方法：

### create_session(...)

输入只允许：

- `topic: str | None = None`
- `metadata: dict[str, Any] | None = None`

约束：

- `session_id` 由 runtime 生成
- `workspace_path` 由 runtime 按固定规则生成，详细规则见 `011-session-history-core`
- 不允许外部传入 `session_id`
- 不允许外部传入 `workspace_path`
- 不允许外部传入 `messages`

返回：

- `SessionSnapshot`

### run(...)

输入模型 `RunRequest` 最小字段：

- `session_id`
- `user_input`
- `attachments`
- `metadata`

约束：

- 不传 `topic_id`
- 不传 `skill_name`
- 不传 `skill_names[]`
- skill 选择由 agent 自主完成
- skills 来源固定为 builtin skills + 当前 workspace skills

返回模型 `RunResult` 最小字段：

- `session_id`
- `final_text`
- `tool_calls`
- `artifacts`

约束：

- `tool_calls` 只保留轻量摘要，不暴露 provider 原始对象
- `artifacts` 只保留本轮关键文件路径引用

### get_session_snapshot(...)

输入：

- `session_id`

返回：

- `SessionSnapshot`

### reset_session(...)

输入：

- `session_id`

行为：

- 只重置 session 的内存/历史状态
- 不删除工作目录
- 不删除业务数据目录

## 组件协作边界

- `SessionManager` 负责 session 生命周期与存取，详细协议见 `011-session-history-core`
- `ContextBuilder` 负责 prompt 与 messages 组装
- `SkillsLoader` 负责 skills 发现、summary 和加载
- `ToolsRegistry` 负责 tools 注册与定义暴露
- `LoopRunner` 负责真正的 tool-calling loop

## 错误边界

整体风格贴近 `nanobot`：

- 子组件内部优先容错继续并记录日志
- 普通工具失败不升级为 runtime 异常
- 达到最大轮数不视为异常，而是走兜底文本

### 子组件容错规则

- bootstrap 文件缺失：跳过
- skill 解析失败：标记不可用或跳过
- session 文件读取失败：返回 `None` 或走创建新 session 路径，详细规则见 `011-session-history-core`

### 公开接口层硬错误

只保留极少数硬错误：

- `SessionNotFoundError`
- `ProviderCallError`
- `RuntimeInitializationError`

不做：

- 完整异常树
- run 状态模型
- 总 run timeout

## 验收标准

- 可以创建 `AgentRuntime` 实例
- runtime 内部固定包含 5 个组件边界
- `create_session(...)` 只接受 `topic` 和 `metadata`
- `session_id` 由 runtime 自动生成
- `ContextBuilder.build_system_prompt()` 顺序稳定：
  - identity + runtime rules
  - bootstrap files
  - skills summary
- bootstrap 四件套缺失时不会报错
- `build_messages()` 顺序稳定：
  - system
  - history
  - current user message
- `runtime context` 只注入时间和 `session_id`
- `run(...)` 不接受显式 skill 指定
- `RunResult` 返回：
  - `session_id`
  - `final_text`
  - `tool_calls`
  - `artifacts`
- runtime 只保留对 `011` 和 `012` 的依赖引用，不重复定义 session/history 或 memory/context 细节
- session 不存在时，对外接口抛 `SessionNotFoundError`
- 普通 tool 失败不升级为 runtime 异常
