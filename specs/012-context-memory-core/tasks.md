# 012 Context Memory Core Tasks

## 当前任务分组

- [x] `012-A`：定义长期记忆对象
  固定 `MEMORY.md / HISTORY.md` 的存储位置、内容形态和 session 级目录结构。
- [x] `012-B`：定义超窗整理策略
  固定 token 预算公式、`target`、安全边界与 chunk 选择路径。
- [x] `012-C`：定义记忆注入顺序
  固定 memory 在 `ContextBuilder` 中的位置和与短期 history、skills summary 的关系。
- [x] `012-D`：定义记忆更新时机
  固定前检查 + 后台补一次的调度策略。
- [x] `012-E`：定义 consolidation agent 协议
  固定输入材料、输出字段和 raw archive fallback。
- [x] `012-F`：定义运行参数
  固定 `_MAX_CONSOLIDATION_ROUNDS = 5`、`_MAX_FAILURES_BEFORE_RAW_ARCHIVE = 3`、`safety_buffer = 1024`。
- [ ] `012-G`：实现 memory usage rules 注入
  将近似参考 `nanobot memory skill` 的 memory rules 作为 `# Memory` section 的固定组成部分注入 prompt。
- [ ] `012-H`：实现真实 memory consolidation agent
  将 `current_memory + messages_text -> history_entry + memory_update` 的独立 consolidator agent 接入 runtime。
- [ ] `012-I`：实现 consolidator 默认接入
  将 pre-check / post-check 的 memory consolidator 默认接入 `AgentRuntime` 与 `LoopRunner`。

## 测试与验收

- [x] 长期记忆结构测试
- [x] 超窗治理策略测试
- [x] 记忆注入顺序测试
- [x] 记忆更新时机测试
- [x] consolidation agent 协议测试
- [x] raw archive fallback 测试
- [x] 前检查 + 后台补一次 调度测试
- [ ] memory rules 注入测试
- [ ] runtime 默认注入 consolidator 测试
- [ ] consolidation 成功后的文件更新与游标推进测试
- [ ] consolidation 失败不推进游标测试

## 实现收口

- [x] memory/context 子系统边界已落地
- [ ] 真实 consolidator agent 已落地
- [ ] runtime / loop 默认 consolidator 接入已落地
- [x] `acceptance.md` 已与最新设计同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成
- 依赖 `011-session-history-core` 已完成

## 备注

- 当前 feature 只定义长期记忆与上下文治理，不引入外部检索系统。
