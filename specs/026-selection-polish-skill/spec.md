# 026 Selection Polish Skill

## 背景

右侧文案编辑区已经升级为单文档白板式 Markdown 编辑器，但当前仍缺少针对局部文本的 AI 润色能力。用户需要在不重写整篇文案的前提下，选中一小段内容并输入本次要求，由 agent 基于整篇上下文返回替换文本。

## 目标

- 提供一个 `selection-polish` skill，专门处理文案选区的局部润色
- 读取整篇文案上下文，但只返回当前选区的替换文本
- 允许用户在前端输入本次润色要求，不把固定提示词写死在 skill 中
- 让前端直接替换当前选区，并复用现有 `copy_draft.json` 自动保存链路
- 让中间对话流追加一条本次润色的结果消息

## 非目标

- 整篇文案重写
- 直接写 `copy_draft.json`
- 独立的流式选区润色协议
- 复杂文档差异比对

## 用户故事

- 作为运营人员，我希望在文案区选中一句话后，输入“更口语一点”这类要求，只润色这一段。
- 作为运营人员，我希望润色时 agent 能理解整篇文案上下文，而不是孤立改一句话。
- 作为开发者，我希望前端继续掌握文案真相写回，skill 只返回结构化替换结果。

## 输入输出

- 输入：
  - 当前整篇文案 Markdown
  - 当前选中文本
  - 用户本次输入的润色要求
- 输出：
  - `replacement_text`
  - `message`

## 约束

- `selection-polish` 只负责局部润色，不得重写整篇文案
- skill 必须读取整篇上下文，但只输出当前选区的替换文本
- skill 不得直接写 `copy_draft.json`
- skill 不得要求用户手动复制整篇文案
- 返回格式固定为 JSON：
  - `replacement_text`
  - `message`
- 选区润色通过专用接口触发，不走普通 run 文本解析路径
- 前端是选区替换的唯一执行者，替换后再通过既有自动保存写回 `copy_draft.json`

## 前端交互

- 用户在右侧文案编辑区选中非空文本时，出现浮动“AI 润色”入口
- 点击后弹出提示词输入框
- 用户输入本次润色要求并提交后，前端调用专用接口
- 成功后：
  - 直接替换当前选区
  - 保持当前编辑上下文
  - 继续触发自动保存
- 失败时直接提示错误，不改动原文

## 后端接口

### `POST /api/topics/{topic_id}/copy-draft/polish-selection`

输入：

- `topic_title`
- `selected_text`
- `instruction`
- `document_markdown`

返回：

- `topic_id`
- `topic_title`
- `replacement_text`
- `message`
- `updated_at`

行为：

- resolve 当前 topic 对应 session
- 触发一次 `selection-polish` skill
- 读取整篇上下文，但只返回选区替换文本
- 不直接修改 workspace 文案文件
- 向 session history 追加一条 assistant 结果消息，但不保留内部 prompt 消息

## 验收标准

- 选中右侧文案区文本后，可触发“AI 润色”
- 用户可输入本次润色提示词
- 返回结果只替换选区，不改其它正文
- 成功后中间对话流会新增一条结果消息
- 失败时不会污染 `copy_draft.json`
