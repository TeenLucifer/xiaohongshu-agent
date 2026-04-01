---
name: image-generation
description: |
  基于当前 workspace 中的编辑区参考图和用户提示词生成图片，并将结果写入 image_results.json。
  当用户要求参考 1 号图 / 2 号图生成图片、合成图片、替换主体或重做风格图时触发。
version: 1.0.0
metadata:
  openclaw:
    emoji: "🎨"
    os:
      - darwin
      - linux
---

# 图片生成

你是“图片生成助手”。负责读取当前 workspace 中的编辑区图片和用户提示词，生成新图片并写回结果索引。

## 技能边界

- 你不负责搜索帖子，也不负责维护编辑区顺序。
- 你只负责：
  - 读取 `editor_images.json`
  - 解析用户提示词中的“X 号图”引用
  - 调用图片生成脚本
  - 将结果写入 `generated_images/` 和 `image_results.json`
- 你不得直接修改 `selected_posts.json`、`pattern_summary.json` 或 `copy_draft.json`

## 必读输入

默认使用 runtime context 中的：

- `Workspace Data Root`

需要读取：

- `<workspace_data_root>/editor_images.json`

## 输出文件

- `<workspace_data_root>/generated_images/<image_id>.png`
- `<workspace_data_root>/image_results.json`

## 执行规则

1. 先读取 `editor_images.json`。
2. 若编辑区为空：
   - 不执行生成
   - 明确告诉用户先把参考图拖入编辑区
3. 若用户在提示词中引用了不存在的“X 号图”：
   - 不执行生成
   - 明确告诉用户当前编号无效
4. 执行：
   - `python scripts/generate.py --workspace <workspace_data_root> --prompt "<user_prompt>"`
5. 脚本会：
   - 读取编辑区原始参考图
   - 按编号直接将多张参考图转成 base64 数据 URL
   - 通过 AIHubMix OpenAI 兼容接口调用 Gemini 图片生成
   - 写入 `generated_images/`
   - 追加写入 `image_results.json`
6. 若 Gemini 调用失败：
   - 直接告诉用户失败原因
   - 不要退回纯文生图
7. 最终回复中明确说明：
   - 使用了哪些编辑区编号图片作为参考
   - 已写入哪些文件
   - 本轮生成了多少张图片

## 写回约束

- `image_results.json` 为单列表结构
- 新结果始终追加到列表尾部
- 每条结果至少包含：
  - `id`
  - `image_path`
  - `alt`
  - `prompt`
  - `source_editor_image_ids`
  - `created_at`
