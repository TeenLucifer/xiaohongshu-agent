# 014 Agent Tools Core Tasks

## 当前状态

- [x] `014-agent-tools-core` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立 `Tool` 基类与 `ToolsRegistry`，固定默认工具注册和执行上下文边界。
- [x] 完成文件系统工具集：`read_file`、`write_file`、`edit_file`、`list_dir`。
- [x] 固定文件系统权限边界，将路径限制在 session 工作目录、临时目录和 skill 目录内，并默认放开项目根目录 `skills/`。
- [x] 完成 `exec` 工具、allowlist、deny guard、workspace 越界拦截和默认超时策略，并明确仅通过 `working_dir` 切目录。
- [x] 统一工具层参数校验、错误表达与输出截断行为。
- [x] `write_file` 已支持两类输入：
  - 文本字符串原样写入
  - `dict/list` 自动序列化为 JSON 文件

## 当前待办

- [ ] 当前无进行中的 `014` 子任务；后续如有工具边界或执行策略调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
