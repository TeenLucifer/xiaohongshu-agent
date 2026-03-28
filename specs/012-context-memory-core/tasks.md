# 012 Context Memory Core Tasks

## 当前状态

- [x] `012-context-memory-core` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立 `MEMORY.md / HISTORY.md` 的 session 级存储结构与长期记忆注入顺序。
- [x] 固定 token budget、target、安全边界和 chunk 选择策略。
- [x] 将 memory usage rules 注入 `# Memory` section，并与长期记忆内容一起进入 prompt。
- [x] 实现真实 memory consolidation agent，并将 pre-check / post-check 默认接入 runtime 与 loop。
- [x] 建立 memory trace 事件，上报 budget、target、consolidation 结果与 cursor 变化。

## 当前待办

- [ ] 当前无进行中的 `012` 子任务；后续如有 memory 策略或上下文治理调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
