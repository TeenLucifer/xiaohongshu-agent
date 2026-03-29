# 010 Agent Runtime Foundation Tasks

## 当前状态

- [x] `010-agent-runtime-foundation` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立 `AgentRuntime` 薄宿主层，固定 runtime 内部组件边界与公开接口。
- [x] 建立 `ContextBuilder`，固定 system prompt、runtime metadata 和静态 prompt YAML 组织方式。
- [x] 明确命令使用规则与可访问目录提示，固定禁止 `cd/&&/ls/cat` 并要求通过 `exec.working_dir` 切目录。
- [x] 完成 provider 骨架接入，支持最小 OpenAI-compatible 非流式 + tool calling 模式。
- [x] 建立统一错误边界与最小结果模型，供后续 session、memory、loop、tools、skills 复用。
- [x] 引入统一时间入口，固定 `Asia/Shanghai` 为默认时间来源并接入相关子系统。

## 当前待办

- [ ] 当前无进行中的 `010` 子任务；后续如有 runtime 基础边界调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
