# 011 Session History Core Tasks

## 当前状态

- [x] `011-session-history-core` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立 `Session`、`SessionSnapshot`、`SessionManager`，固定 session 作为 runtime 工作单元。
- [x] 完成短期历史追加、读取、清空与 `last_consolidated` 游标规则。
- [x] 完成 `jsonl` 持久化、容错加载与 workspace 目录存在性保证。
- [x] 固定 tool 消息合法边界、超长 tool 结果处理与 runtime context 持久化剥离规则。

## 当前待办

- [ ] 当前无进行中的 `011` 子任务；后续如有 session/history 边界调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
