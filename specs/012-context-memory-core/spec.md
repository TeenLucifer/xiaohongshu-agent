# 012 Context Memory Core

## 背景

仅依赖 `Session.messages` 作为短期记忆不足以支撑长会话。长期记忆机制和上下文窗口治理需要单独设计，否则后续 `ContextBuilder` 和 `LoopRunner` 会继续耦合。

## 目标

- 定义长期记忆在 runtime 中的角色
- 定义超过上下文窗口后的整理策略
- 定义长期记忆如何进入 `ContextBuilder`
- 定义短期历史、长期记忆与 skills summary 的上下文优先级

## 非目标

- tools 实现
- skills 协议
- 后端业务持久化
- 向量数据库或复杂检索系统

## 用户故事

- 作为实现者，我希望长会话不会无限增长，也不会因为上下文窗口溢出而失去关键事实。
- 作为后续实现者，我希望长期记忆和短期历史的边界明确，便于后续扩展总结、复盘和跨轮工作上下文。

## 输入输出

- 输入：session 历史、上下文窗口约束、需要沉淀的历史片段
- 输出：长期记忆摘要、可用于本轮 prompt 的上下文组合

## 约束

- `Session.messages` 仍作为短期记忆来源
- 长期记忆采用两层结构：
  - `MEMORY.md`
  - `HISTORY.md`
- 长期记忆按 session 独立存储：
  - `data/sessions/<session_id>/memory/`
- 长期记忆不是无限原始日志，而是整理后的摘要/事实
- 当短期历史超过上下文窗口时，必须有明确的整理路径
- `ContextBuilder` 在 system prompt 中可以注入长期记忆上下文
- 首版不做向量检索
- consolidation 机制与 `nanobot` 保持一致

## 讨论范围

### 长期记忆

需要固定：

- 长期记忆存储位置
- 长期记忆内容形态
- 长期记忆何时更新
- 长期记忆如何被重新注入 prompt

已定规则：

- `MEMORY.md` 保存完整更新版长期记忆
- `HISTORY.md` 追加归档 entry
- `MEMORY.md` 为 markdown
- `MEMORY.md` 不预设固定 section
- 每次 consolidation 返回完整更新版 `memory_update`
- `HISTORY.md` 每次 consolidation 追加一条 `history_entry`
- `history_entry` 必须以 `[YYYY-MM-DD HH:MM]` 开头
- `# Memory` section 不仅注入 `MEMORY.md` 内容，也注入固定的 memory usage rules
- memory usage rules 近似参考 `nanobot/skills/memory/SKILL.md`，至少明确：
  - `MEMORY.md` 记录长期事实、稳定偏好、持续上下文
  - `HISTORY.md` 是追加式历史日志，不直接注入 prompt
  - 搜索历史优先查 `HISTORY.md`
  - 重要稳定事实应写入 `MEMORY.md`
  - memory consolidation 由 runtime 内建的 consolidator 负责，而不是由 skill 执行

### 上下文窗口治理

需要固定：

- 何时认为短期历史过长
- 是裁剪、摘要还是沉淀后再裁剪
- history 与 memory 的注入顺序
- 哪些内容必须优先保留

已定规则：

- 使用 token 估算判断是否超预算
- 预算公式固定为：
  - `budget = context_window_tokens - max_completion_tokens - 1024`
- consolidation 目标压缩线固定为：
  - `target = budget // 2`
- `max_completion_tokens` 跟模型配置走
- `safety_buffer = 1024`
- 使用动态消息边界，而不是固定窗口长度
- 优先在安全边界切分，避免切断 tool 调用链
- 短期历史来自 `Session.get_history(...)`
- 长期记忆通过 `MEMORY.md` 内容和 memory usage rules 一起注入 system prompt

## consolidation agent

- 使用独立的 `memory consolidation agent`
- 输入包含：
  - 当前 `MEMORY.md`
  - 待整理 message chunk 的文本化表示
- 输出协议固定为：
  - `history_entry`
  - `memory_update`
- 连续失败后允许 raw archive fallback 写入 `HISTORY.md`
- `memory consolidation agent` 是 runtime 内建能力，不属于 skills 子系统
- consolidator 必须被默认接入 runtime / loop
- run 前必须执行一次 pre-check
- run 后必须调度一次 post-check
- consolidator 必须支持向可选 trace sink 上报联调摘要事件
- consolidation 成功后必须：
  - 追加写入 `HISTORY.md`
  - 更新 `MEMORY.md`
  - 推进 `last_consolidated`
- consolidation 失败时不得错误推进 `last_consolidated`
- trace 首版至少应覆盖：
  - pre-check / post-check 是否执行
  - token 估算值
  - `budget`
  - `target`
  - 是否触发 consolidation
  - 选中的消息数量
  - consolidation 成功/失败
  - `last_consolidated` 前后变化

## 调度策略

- 运行前检查一次是否超预算
- 运行后后台再补一次 consolidation
- 参数固定贴 `nanobot`：
  - `_MAX_CONSOLIDATION_ROUNDS = 5`
  - `_MAX_FAILURES_BEFORE_RAW_ARCHIVE = 3`

## ContextBuilder 注入顺序

system prompt 中的顺序固定为：

1. `identity`
2. `bootstrap`
3. `memory`
4. `always skills`
5. `skills summary`

## 验收标准

- 长期记忆与短期历史边界清晰
- 超上下文窗口时有明确处理路径
- `ContextBuilder` 能稳定接入长期记忆
- `MEMORY.md` 与 `HISTORY.md` 路径固定
- consolidation 协议固定为 `history_entry / memory_update`
- 预算公式、`target` 和调度策略固定
- 不需要引入向量库也能完成首版治理
- memory rules 已作为 `# Memory` section 的固定组成部分
- consolidator 已被定义为 runtime 默认接入能力，而不只是预留协议
- memory 的关键调度与 consolidation 结果可被 harness trace 稳定观测
