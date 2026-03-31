# 004 Conversation Timeline Tasks

## 当前任务分组

- [x] `004-A`：完成主栏消息模型收敛
  统一 user 消息、agent 消息和内容结果消息的前端展示模型。
- [x] `004-B`：完成主栏聊天化重构
  中间主栏已从日志时间线收敛为轻量聊天流，只保留 user / agent 结果消息。
- [x] `004-C`：完成过程信息退出主界面
  调用过程、工具过程、输入输出摘要和详细日志不再默认出现在主栏。
- [x] `004-D`：完成轻量消息结构
  消息采用小图标 + 文本的轻量结构，整体密度和节奏参考 DeepTutor。
- [x] `004-E`：完成结构型图标与容器级动效统一
  主栏已接入 Lucide 和 Framer Motion 的当前实现边界，不引入细碎动画。
- [x] `004-F`：完成 agent 消息 Markdown 渲染
  主栏 agent 消息需支持 GFM 基础 Markdown，只读显示，不支持原始 HTML。
- [x] `004-G`：完成 final answer 视图收口与工具摘要附着
  主栏 agent 消息已按 user turn 只展示 final answer，中间 assistant 迭代不再展示；tool 调用仅以附着在 final answer 下方的折叠摘要存在。

## 测试与验收

- [x] 主栏聊天流渲染测试通过
- [x] 主界面不展示过程信息测试通过
- [x] 轻量消息结构测试通过
- [x] 结构型图标与容器级动效测试通过
- [x] agent 消息 Markdown 渲染测试
- [x] user 文本消息不受 Markdown 渲染影响测试
- [x] final answer 过滤与 tool 摘要折叠展示测试

## 实现收口

- [x] 主栏消息组件和 Mock 会话数据已落地
- [x] 简化对话流的最终形态已落地
- [x] `acceptance.md` 已与当前实现同步

## 依赖

- 依赖 `001-topic-workspace` 已完成

## 备注

- 当前不接入独立 debug 视图。
