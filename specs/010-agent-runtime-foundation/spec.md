# 010 Agent Runtime Foundation

## 背景

前端工作台已经基本稳定，下一阶段需要先建立主 agent 的基础运行宿主层，为后续 tools、skills、loop 和本地 harness 提供稳定边界。

本 feature 参考 `nanobot` 的总体形态，但不照搬其聊天渠道模型。本项目的 runtime 以 `Session` 为真正工作单元，`topic` 只是 session metadata。

首版 provider 采用 OpenAI-compatible 方向，但只覆盖最小可联调能力：

- 非流式 chat completion
- tool calling
- 基础环境变量配置

## 目标

- 建立一个薄的 `AgentRuntime` 宿主层
- 固定内部 6 个组件边界：
  - `SessionManager`
  - `ContextBuilder`
  - `SkillsLoader`
  - `ToolsRegistry`
  - `LoopRunner`
  - `Provider / ModelClient`
- 固定 `Session` 数据边界
- 固定 `ContextBuilder` 的系统提示词与消息组装顺序
- 固定 runtime 对外最小接口和输入输出模型
- 固定 provider 的最小适配边界与默认配置来源
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
- `Provider / ModelClient`

`AgentRuntime` 负责：

- 创建和重置 session
- 基于 `session_id` 运行一次 agent 调用
- 读取 session 快照
- 串联 session、context、skills、tools、provider、loop
- 通过内部轻量时间入口为 runtime 子系统提供统一时间来源

`AgentRuntime` 不负责：

- tools 具体实现
- skills 协议设计
- loop 内部迭代逻辑
- provider 之外的上层产品接入策略
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
2. `memory`
3. `always skills`
4. `skills summary`

### memory / always skills / skills summary

memory 规则：

- 长期记忆来自 `012-context-memory-core`
- 以独立 memory section 注入 system prompt
- `# Memory` section 同时包含长期记忆内容和固定的 memory usage rules
- memory usage rules 可来自内部 YAML prompt 配置

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
- summary 中至少包含：
  - `name`
  - `description`
  - `location`
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
- `Workspace Path`

并明确标记为：

- metadata only
- not instructions

其中：

- `Current Time` 来自 runtime 内部统一时间入口
- 首版固定使用 `Asia/Shanghai`
- 首版不做时区配置化

### identity + runtime rules 约束补充

`ContextBuilder` 的系统级规则必须明确：

- agent 只能在当前 `session workspace` 内工作
- 不要假设可访问项目根目录、宿主根目录或任意绝对路径
- 查看目录优先使用 `list_dir`
- 读取文件优先使用 `read_file`

### 静态 prompt 配置边界

- `ContextBuilder` 中的静态提示词文案可以由内部 YAML 配置提供
- 静态提示词配置只承载固定文案，不承载运行时条件逻辑
- 动态拼装职责仍保留在 `ContextBuilder`：
  - memory
  - always skills
  - skills summary
  - runtime context

### 内部时间入口边界

- runtime 允许持有一个很薄的内部时间 helper，用于统一提供当前时间
- 该 helper 只负责固定时区下的“当前时间”和基础格式一致性
- 首版固定时区为 `Asia/Shanghai`
- 不引入复杂时钟服务、调度器或可配置时区管理
- session/history、memory、trace 等子系统应复用同一时间来源，而不是各自直接取系统时间

### workspace_path 注入边界

- `workspace_path` 由 runtime/session 内部提供给 `ContextBuilder`
- `workspace_path` 不进入 `RunRequest`
- runtime 负责把当前 session 的 `workspace_path` 注入到本轮 message 构建过程

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

## Provider 骨架边界

### Provider / ModelClient

provider 是 `010` 的 runtime 骨架组件，不单独拆新 feature。

首版范围固定为：

- OpenAI-compatible 接口
- 非流式 chat completion
- tool calling
- 基础配置与环境变量读取

provider 负责：

- 接收 `messages + tool_definitions`
- 发起一次模型调用
- 将 provider 原始响应收敛为 `LoopModelResponse`

provider 不负责：

- 流式输出
- 多模态输入
- 模型路由与重试策略
- 供应商特有扩展能力

### Provider 配置

首版默认从环境变量读取：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（可选）
- `OPENAI_MODEL`

同时允许在 runtime 初始化时显式注入 provider 或 model client 覆盖默认值。

### Provider 适配约束

- `LoopRunner` 仅依赖 `LoopModelClient` 协议，不直接耦合具体 SDK
- provider 默认实现必须能解析：
  - assistant 文本内容
  - tool calls
- provider 原始响应对象不得穿透到 `RunResult`

## 组件协作边界

- `SessionManager` 负责 session 生命周期与存取，详细协议见 `011-session-history-core`
- `ContextBuilder` 负责 prompt 与 messages 组装
- `SkillsLoader` 负责 skills 发现、summary 和加载
- `ToolsRegistry` 负责 tools 注册与定义暴露
- `Provider / ModelClient` 负责真实模型调用适配
- `LoopRunner` 负责真正的 tool-calling loop

## 错误边界

整体风格贴近 `nanobot`：

- 子组件内部优先容错继续并记录日志
- 普通工具失败不升级为 runtime 异常
- 达到最大轮数不视为异常，而是走兜底文本

### 子组件容错规则

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
- runtime 内部固定包含 6 个组件边界
- `create_session(...)` 只接受 `topic` 和 `metadata`
- `session_id` 由 runtime 自动生成
- `ContextBuilder.build_system_prompt()` 顺序稳定：
  - identity + runtime rules
  - memory
  - always skills
  - skills summary
- `build_messages()` 顺序稳定：
  - system
  - history
  - current user message
- `runtime context` 只注入时间、`session_id` 和 `workspace_path`
- `run(...)` 不接受显式 skill 指定
- runtime 默认会尝试构造 provider / model client
- provider 缺失必要配置时会返回清晰错误
- `RunResult` 返回：
  - `session_id`
  - `final_text`
  - `tool_calls`
  - `artifacts`
- runtime 只保留对 `011` 和 `012` 的依赖引用，不重复定义 session/history 或 memory/context 细节
- session 不存在时，对外接口抛 `SessionNotFoundError`
- 普通 tool 失败不升级为 runtime 异常
