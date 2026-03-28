# 010 Agent Runtime Foundation Tasks

## 当前任务分组

- [x] `010-A`：定义 `AgentRuntime` 薄宿主层
  固定 runtime 内部 6 个组件边界，并明确宿主层只做协调。
- [x] `010-B`：定义 `ContextBuilder`
  固定 system prompt 与 message list 的组装顺序，以及 bootstrap 四件套规则。
- [x] `010-C`：定义 runtime 对外接口
  固定 `create_session(...)`、`run(...)`、`get_session_snapshot(...)`、`reset_session(...)` 的最小输入输出。
- [x] `010-D`：定义组件协作边界
  固定 `SessionManager`、`ContextBuilder`、`SkillsLoader`、`ToolsRegistry`、`LoopRunner` 的协调关系。
- [x] `010-E`：定义错误边界
  采用 `nanobot` 风格的容错设计，只在公开接口层保留少量硬错误。
- [x] `010-F`：补 provider 骨架组件
  将 `Provider / ModelClient` 收编进 runtime foundation，并固定最小 OpenAI-compatible 适配边界。
- [x] `010-G`：补 provider 默认配置
  固定环境变量默认读取与显式注入覆盖策略。

## 测试与验收

- [x] runtime 初始化测试
- [x] `create_session(...)` 输入边界测试
- [x] `session_id` 自动生成测试
- [x] `ContextBuilder.build_system_prompt()` 顺序测试
- [x] bootstrap 文件缺失容错测试
- [x] `build_messages()` 顺序测试
- [x] `runtime context` 注入测试
- [x] `run(...)` 输入输出模型测试
- [x] 组件协作边界测试
- [x] `SessionNotFoundError` 抛出测试
- [x] provider config/env 测试
- [x] provider 适配与响应解析测试
- [x] runtime 默认 provider 构造测试
- [x] provider 缺配置错误测试

## 实现收口

- [x] `spec.md` 中的 runtime 宿主边界已落地
- [x] `RunRequest` / `RunResult` 结构已落地
- [x] `011` / `012` 依赖边界已正确引用
- [x] provider 骨架已落地
- [x] `acceptance.md` 已与 provider 实现同步

## 依赖

- 依赖 `000-foundation` 已完成

## 备注

- 当前 feature 只处理 runtime foundation，不实现 tools、skills loader、loop、session/history 细节和 memory/context 治理。
- provider 已作为 `010` 骨架组件落地，当前提供最小 OpenAI-compatible 非流式 + tool calling 适配能力。
