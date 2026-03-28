# 012 Context Memory Core Acceptance

## 手工验收

1. 构造一个有较长历史的 session
2. 确认短期历史和长期记忆有明确边界
3. 确认 session 的 memory 目录固定为：
   - `data/sessions/<session_id>/memory/MEMORY.md`
   - `data/sessions/<session_id>/memory/HISTORY.md`
4. 触发一次超上下文窗口场景
5. 确认系统按 token 预算公式判断超预算：
   - `context_window_tokens - max_completion_tokens - 1024`
6. 确认系统使用动态安全边界选择 chunk，而不是固定窗口长度
7. 检查 consolidation agent 输入
8. 确认包含当前 `MEMORY.md` 和待整理 message chunk 的文本化表示
9. 检查 consolidation agent 输出
10. 确认固定为：
   - `history_entry`
   - `memory_update`
11. 确认 `history_entry` 以 `[YYYY-MM-DD HH:MM]` 开头
12. 确认 `memory_update` 会覆盖更新 `MEMORY.md`
13. 确认 `history_entry` 会追加写入 `HISTORY.md`
14. 检查 `ContextBuilder`
15. 确认长期记忆按固定顺序进入 prompt：
   - identity
   - bootstrap
   - memory
   - always skills
   - skills summary
16. 确认 `# Memory` section 同时包含长期记忆内容和固定的 memory usage rules
17. 确认 memory rules 至少说明：
   - `MEMORY.md` 记录长期事实
   - `HISTORY.md` 是追加式历史
   - 搜索历史优先查 `HISTORY.md`
   - consolidator 由 runtime 内建能力负责
18. 确认采用“运行前检查 + 运行后后台补一次”的调度策略
19. 构造连续 consolidation 失败场景
20. 确认系统会走 raw archive fallback，并将原始归档写入 `HISTORY.md`
21. 构造一次真实超预算 run
22. 确认 run 前会尝试 consolidation，run 后会调度 post-check
23. 确认 consolidation 成功后：
   - `HISTORY.md` 增加新 entry
   - `MEMORY.md` 被更新
   - `last_consolidated` 前移
24. 确认首版方案不依赖向量库或外部检索系统

## 自动化验收

- 长期记忆结构测试通过
- 超窗治理策略测试通过
- 记忆注入顺序测试通过
- 记忆更新时机测试通过
- consolidation agent 协议测试通过
- raw archive fallback 测试通过
- 前检查 + 后台补一次 调度测试通过
- memory rules 注入测试通过
- runtime 默认注入 consolidator 测试通过
- consolidation 成功后的文件更新与游标推进测试通过
- consolidation 失败不推进游标测试通过

## 已知限制

- 当前不做向量检索
- 当前不做复杂记忆检索排序
