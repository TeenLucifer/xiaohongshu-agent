# 011 Session History Core Tasks

## 当前任务分组

- [x] `011-A`：定义 `Session` 与 `SessionSnapshot`
  固定字段、`uuid4` 生成规则、`last_consolidated`、消息类型和默认目录规则。
- [x] `011-B`：定义 `SessionManager`
  固定 create/load/save/invalidate/list/snapshot 的职责边界和轻量快照返回规则。
- [x] `011-C`：定义消息追加与读取规则
  固定 `add_message(...)`、`get_history(...)`、`clear()`、`reset_session(...)` 和游标规则。
- [x] `011-D`：定义历史合法边界处理
  处理孤立 tool 结果、超长 tool 消息、持久化字段保留和 runtime context 持久化剥离。
- [x] `011-E`：定义 session 持久化与容错
  固定 `jsonl` 结构、`last_consolidated` 持久化、save 重写策略、加载失败路径和容错行为。

## 测试与验收

- [x] `Session` 结构测试
- [x] `SessionSnapshot` 结构测试
- [x] `session_id = uuid4` 测试
- [x] `last_consolidated` 默认值测试
- [x] `SessionManager` 职责边界测试
- [x] 消息追加测试
- [x] `get_history(...)` 按游标返回合法切片测试
- [x] tool 消息截断测试
- [x] `jsonl` 结构测试
- [x] `last_consolidated` 持久化读写测试
- [x] `save` 重写策略测试
- [x] `reset_session(...)` 行为测试
- [x] consolidation 失败时游标不前移测试
- [x] session 加载失败容错测试
- [x] session 创建即落盘 workspace 目录测试
- [x] session 加载成功时 workspace 缺失补建测试

## 实现收口

- [x] session/history 子系统边界已落地
- [x] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成

## 备注

- 当前 feature 只处理短期记忆与历史存取，不处理长期记忆。
