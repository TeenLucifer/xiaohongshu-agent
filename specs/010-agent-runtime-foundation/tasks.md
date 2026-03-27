# 010 Agent Runtime Foundation Tasks

## 当前任务分组

- [ ] `010-A`：定义 `AgentRuntime` 薄宿主层
  固定 runtime 内部 5 个组件边界，并明确宿主层只做协调。
- [ ] `010-B`：定义 `ContextBuilder`
  固定 system prompt 与 message list 的组装顺序，以及 bootstrap 四件套规则。
- [ ] `010-C`：定义 runtime 对外接口
  固定 `create_session(...)`、`run(...)`、`get_session_snapshot(...)`、`reset_session(...)` 的最小输入输出。
- [ ] `010-D`：定义组件协作边界
  固定 `SessionManager`、`ContextBuilder`、`SkillsLoader`、`ToolsRegistry`、`LoopRunner` 的协调关系。
- [ ] `010-E`：定义错误边界
  采用 `nanobot` 风格的容错设计，只在公开接口层保留少量硬错误。

## 测试与验收

- [ ] runtime 初始化测试
- [ ] `create_session(...)` 输入边界测试
- [ ] `session_id` 自动生成测试
- [ ] `ContextBuilder.build_system_prompt()` 顺序测试
- [ ] bootstrap 文件缺失容错测试
- [ ] `build_messages()` 顺序测试
- [ ] `runtime context` 注入测试
- [ ] `run(...)` 输入输出模型测试
- [ ] 组件协作边界测试
- [ ] `SessionNotFoundError` 抛出测试

## 实现收口

- [ ] `spec.md` 中的 runtime 宿主边界已落地
- [ ] `RunRequest` / `RunResult` 结构已落地
- [ ] `011` / `012` 依赖边界已正确引用
- [ ] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `000-foundation` 已完成

## 备注

- 当前 feature 只处理 runtime foundation，不实现 tools、skills loader、loop、session/history 细节和 memory/context 治理。
