# 011 Session History Core

## 背景

`Session`、`SessionSnapshot`、`SessionManager` 和短期消息历史已经形成独立复杂度，不适合继续混在 runtime foundation 或 loop feature 中。需要单独定义 session 历史子系统的边界。

## 目标

- 固定 `Session` / `SessionSnapshot` 的结构
- 固定 `SessionManager` 的职责边界
- 固定 session 的持久化格式与默认目录规则
- 固定消息类型、追加规则和 history 读取规则
- 固定 tool 消息截断与历史合法边界处理

## 非目标

- 长期记忆
- 超上下文窗口后的摘要/压缩策略
- loop 控制逻辑
- tools 执行逻辑
- 后端业务对象持久化

## 用户故事

- 作为实现者，我希望短期记忆和历史持久化有单独边界，不与 runtime 或 loop 混在一起。
- 作为后续实现者，我希望 session 文件损坏、tool 消息过长、历史裁剪等问题都有独立规则。

## 输入输出

- 输入：session 元数据、追加消息、session 标识
- 输出：`Session`、`SessionSnapshot`、合法的历史消息切片

## 约束

- runtime 主工作单元是 `Session`
- `session_id` 固定使用 `uuid4` 生成
- `topic` 只是 session metadata，不是主键
- `Session.messages` 只允许：
  - `user`
  - `assistant`
  - `tool`
- `system` 不进入 session 历史
- `tool` 消息超长时保留截断后的完整结果
- session 默认工作目录规则保持：
  - `data/sessions/<session_id>/`
- `SessionSnapshot` 不包含额外统计字段

## Session 字段

### Session

- `session_id`
- `topic`
- `messages`
- `last_consolidated`
- `workspace_path`
- `created_at`
- `updated_at`
- `metadata`

约束：

- `last_consolidated: int`
- 默认值为 `0`
- 表示已成功沉淀进长期记忆的消息边界下标

### SessionSnapshot

- `session_id`
- `topic`
- `workspace_path`
- `created_at`
- `updated_at`
- `metadata`

约束：

- 不新增 `message_count`
- 不新增 `last_message_at`
- 不新增统计或聚合字段

## SessionManager 边界

`SessionManager` 设计贴近 `nanobot`，只负责 session 生命周期与存取：

- `create`
- `get_or_create`
- `load`
- `save`
- `invalidate`
- `list_sessions`
- `snapshot`

不负责：

- 上下文组装
- tools 执行
- skills 加载
- loop 控制
- 长期记忆治理

约束：

- `list_sessions` 只返回轻量快照
- 不在 `list_sessions` 中额外拼统计信息

## 历史消息规则

- `Session` 自身负责：
  - `add_message(...)`
  - `get_history(...)`
  - `clear()`
  - 必要的历史合法边界处理
- `get_history(...)` 返回面向模型输入的合法历史切片
- `get_history(...)` 默认只返回 `messages[last_consolidated:]` 的未沉淀部分
- 历史切片应避免前置孤立的 `tool` 结果
- 超长 `tool` 结果在入 session 前截断
- `runtime context` 不进入持久化历史正文
- 持久化消息中保留以下字段：
  - `tool_calls`
  - `tool_call_id`
  - `name`

### reset_session(...)`

重置规则固定为：

- 清空 `messages`
- 将 `last_consolidated` 重置为 `0`
- 保留 `session_id`
- 保留 `topic`
- 保留 `workspace_path`
- 保留 `metadata`
- 更新时间戳

### consolidation 游标规则

- `last_consolidated` 不表示固定窗口长度
- `last_consolidated` 表示已成功沉淀进长期记忆的历史边界下标
- consolidation 成功后，`last_consolidated` 才前移到新的边界位置
- consolidation 失败时，`last_consolidated` 不前移

## 持久化与容错

- session 采用 `jsonl` 格式持久化
- `jsonl` 结构贴近 `nanobot`
  - 第一行写 metadata
  - 后续每行写一条 message
- metadata 行必须保存 `last_consolidated`
- 内存中维护完整 `Session`
- 每次 `save` 重写整个 session 文件
- session 文件读取失败时：
  - 记录日志
  - 返回 `None`
  - 由上层决定是否走新建 session 路径
- session 文件问题不应直接导致整个 runtime 崩溃

## 验收标准

- `Session` / `SessionSnapshot` 字段稳定
- `session_id` 使用 `uuid4`
- `last_consolidated` 字段稳定且默认值为 `0`
- `SessionManager` 职责边界清晰
- 消息类型和追加规则稳定
- `get_history(...)` 能返回从 `last_consolidated` 开始的合法历史切片
- tool 消息超长时能截断
- `jsonl` 第一行是 metadata，后续每行是一条 message
- metadata 行包含 `last_consolidated`
- 每次 `save` 会重写整个 session 文件
- `reset_session(...)` 只清空消息并重置游标，不清空核心元数据
- session 读取失败时能容错继续
