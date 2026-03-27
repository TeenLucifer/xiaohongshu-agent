# 016 Agent Local Harness

## 背景

在没有后端胶水层的情况下，需要先给主 agent 一个本地可运行入口，用于验证 runtime、session、memory、tools、skills 和 loop 是否真正能协同工作。

## 目标

- 提供本地 Python 调用入口
- 提供最小 CLI / smoke harness
- 支持复用已有 `session_id` 运行
- 支持在无 `session_id` 时基于 `topic` 创建 session 再运行
- 输出最终结果、工具调用摘要和关键产物路径

## 非目标

- HTTP API
- 前端联调
- GitHub skill 安装
- 文件化真相层完整回写协议

## 用户故事

- 作为开发者，我希望在没有后端的情况下先把 agent 真正跑起来。
- 作为后续实现者，我希望能快速验证当前 runtime 能否正确加载 skills、执行 loop 并复用 session 历史。

## 输入输出

- Python 入口输入：`session_id`、`user_input`、可选 `attachments`、可选 `metadata`
- CLI 输入：
  - `session_id` 或 `topic`
  - `user_input`
  - 多次 `--attachment <path>`
  - 可选 `--metadata '<json>'`
- 输出：
  - `session_id`
  - `final_text`
  - `tool_calls`
  - `artifacts`

## 约束

- 首版入口以本地 Python 接口为主
- CLI 仅作为很薄的 smoke harness，不作为正式产品入口
- CLI 采用单命令模式，通过 `python -m src.agent.local_harness run ...` 暴露
- CLI 支持两种模式：
  - 传 `session_id` 时复用已有 session
  - 不传 `session_id` 且传 `topic` 时自动创建新 session 再运行
- `session_id` 与 `topic` 互斥：
  - 同时传入时报输入错误
  - 两者都未传入时报输入错误
- `metadata` 在 CLI 中以 JSON 字符串形式传入
- 默认输出为人类可读格式
- 支持 `--json` 输出结构化结果
- 支持 `--verbose` 输出更多 tool 摘要与调试信息
- CLI 退出码固定为：
  - `0` 成功
  - `1` 输入错误
  - `2` 运行失败
- skill 由 agent 自主选择，不在 harness 输入中显式指定

## 验收标准

- 本地可以指定一个 session 直接运行
- 本地可以在只提供 `topic` 时自动创建 session 再运行
- 能看到最终文本结果
- 能看到工具调用摘要
- 能看到关键产物路径
- 能验证可用 skills 已进入当前运行上下文
- 能验证同一 `session_id` 下历史会被复用
- `--json` 与 `--verbose` 行为清晰稳定
