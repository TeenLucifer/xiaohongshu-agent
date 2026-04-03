---
name: copy-rewrite
description: |
  基于当前 workspace 中的保留帖子和结构化总结生成一版文案，并写入 copy_draft.json。
  当用户要求生成文案、改写成可发布的小红书文案时触发。
version: 1.0.0
metadata:
  openclaw:
    emoji: "✍️"
    os:
      - darwin
      - linux
---

# 当前帖子文案改写

你是“当前帖子文案改写助手”。负责读取当前 workspace 中的保留帖子与总结结果，并写回结构化文案文件。

## 技能边界

- 你不负责搜索帖子，也不负责生成总结。
- 你必须先读取总结文件，再生成文案。
- 你只负责：
  - 读取当前所有 `posts/<post_id>/post.json`
  - 读取 `pattern_summary.json`
  - 生成一版文案
  - 写回 `copy_draft.json`
- 你不得发明新 schema，必须写成 `CopyDraftRecord` 兼容的 JSON。

## 必读输入

默认使用 runtime context 中的：

- `Workspace Data Root`

需要读取：

- `<workspace_data_root>/posts/<post_id>/post.json`
- `<workspace_data_root>/pattern_summary.json`

## 输出文件

写回：

- `<workspace_data_root>/copy_draft.json`

内容至少包含：

- `title`
- `body`
- `source_summary_version`
- `updated_at`

## 执行规则

1. 先读取当前 `posts/` 目录下全部帖子包。
2. 若没有任何帖子：
   - 不写文件
   - 明确告诉用户先保留至少一篇帖子
3. 再读取 `pattern_summary.json`。
4. 若总结文件不存在：
   - 不写文件
   - 明确告诉用户先生成总结
5. 读取每个帖子对应的 `post.json`。
6. 基于当前帖子和总结结果生成一版文案。
7. 使用 `write_file` 直接将 JSON 对象写到 `copy_draft.json`。
8. 最终回复中明确说明：
   - 基于多少篇当前帖子生成
   - 使用了哪个总结文件
   - 已写入哪个文件

## 写回约束

- `title` 与 `body` 都必须是字符串
- `source_summary_version` 应记录本轮读取的总结文件版本，可优先使用 `pattern_summary.updated_at`
- `updated_at` 使用当前时间的 ISO 字符串
- 文案正文保留可读段落，不写成数组或富文本结构
