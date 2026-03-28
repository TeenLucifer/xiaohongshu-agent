# 016 Agent Local Harness Tasks

## 当前状态

- [x] `016-agent-local-harness` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立本地 Python 入口与最小 CLI / smoke harness，完成 session/topic 驱动的本地执行路径。
- [x] 统一输出格式、`--json`、`--verbose`、参数校验和退出码策略。
- [x] 完成 `smoke run / smoke test` 的 harness 侧语义规范化，固定为 session 目录自检。
- [x] 建立 `--trace` 与 `--trace-full`，在 session workspace 下生成人类可读联调日志。
- [x] 完成 trace 摘要模式、全量逐轮模式、最小脱敏与 trace 路径终端提示。

## 当前待办

- [ ] 当前无进行中的 `016` 子任务；后续如有本地联调或 trace 能力调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
