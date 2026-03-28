# 013 Agent Loop Runner Tasks

## 当前状态

- [x] `013-agent-loop-runner` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立主 agent loop，完成模型调用、工具调用、消息回灌和 session 保存的最小闭环。
- [x] 固定 loop 停止逻辑，对齐“无 tool call 即结束”和最大轮数兜底文本。
- [x] 完成 batched tool calls 并发执行与按原顺序回灌。
- [x] 接入 skill 自主选择与 memory hook，支持 run 前检查和 run 后补一次 consolidation。
- [x] 建立 loop trace 事件，支持逐轮输入输出、tool 调用摘要与结束原因观测。

## 当前待办

- [ ] 当前无进行中的 `013` 子任务；后续如有 loop 行为或 trace 边界调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
