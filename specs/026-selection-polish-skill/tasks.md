# 026 Selection Polish Skill Tasks

## 当前任务分组

- [x] `026-A`：新增 `selection-polish` skill 文档
  已明确输入、输出、边界和 JSON 返回格式。
- [x] `026-B`：新增专用后端接口
  已提供 `POST /api/topics/{topic_id}/copy-draft/polish-selection`。
- [x] `026-C`：打通前端选区润色交互
  已支持选区浮动入口、提示词弹层、成功替换与自动保存。
- [x] `026-D`：追加中间对话流结果消息
  润色成功后会在会话消息中新增一条 assistant 结果消息。
- [x] `026-E`：完成最小测试与文档联动
  已补接口测试、前端基础回归和跨 feature 文档同步。

## 测试与验收

- [x] 选区润色专用接口测试通过
- [x] 空选区 / 空指令 / 空文案请求校验测试通过
- [x] 文案区基础渲染与内部滚动回归测试通过
- [x] 文案区“AI 润色”入口文案测试通过

## 实现收口

- [x] `selection-polish` 只返回替换文本，不直接写文件
- [x] `copy_draft.json` 的写回仍由前端现有自动保存链路负责
- [x] 中间对话流不暴露内部 prompt
