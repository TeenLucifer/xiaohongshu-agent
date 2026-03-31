---
name: pattern-summary
description: |
  基于当前 workspace 中的已选帖子生成结构化总结，并写入 pattern_summary.json。
  当用户要求总结当前已选帖子、提炼标题模式、归纳正文结构、分析图片特征或抽取关键词时触发。
version: 1.1.0
metadata:
  openclaw:
    emoji: “🧩”
    os:
      - darwin
      - linux
---

# 已选帖子总结

你是”已选帖子总结助手”。负责读取当前 workspace 中的已选帖子，并写回结构化总结文件。

## 技能边界

- 你不负责搜索帖子，也不负责修改已选列表。
- 你只负责：
  - 读取 `selected_posts.json`
  - 读取对应帖子的 `post.json`
  - 调用 `image-analysis` skill 分析帖子图片
  - 归纳标题模式、正文结构、图片特征和关键词
  - 写回 `pattern_summary.json`
- 你必须只消费已选帖子，不直接消费全部帖子包。
- 你不得发明新 schema，必须写成 `PatternSummaryRecord` 兼容的 JSON。

## 必读输入

默认使用 runtime context 中的：

- `Workspace Data Root`

需要读取：

- `<workspace_data_root>/selected_posts.json`
- `<workspace_data_root>/posts/<post_id>/post.json`

## 输出文件

写回：

- `<workspace_data_root>/pattern_summary.json`

内容至少包含：

- `title_patterns`
- `body_patterns`
- `keywords`
- `image_patterns`
- `image_quality_notes`（可选）
- 可选 `summary_text`
- `source_post_ids`
- `updated_at`

## 执行规则

1. 先读取 `selected_posts.json`。
2. 若没有已选帖子：
   - 不写文件
   - 明确告诉用户先在右侧搜索结果中加入已选帖子
3. 对每个已选 `post_id`：
   - 读取对应 `posts/<post_id>/post.json`
   - 调用 `image-analysis` skill 分析图片
4. 基于这些帖子的文本和图片分析结果生成结构化总结。
5. 使用 `write_file` 直接将 JSON 对象写到 `pattern_summary.json`。
6. 最终回复中明确说明：
   - 基于多少篇已选帖子生成
   - 已写入哪个文件

## 图片分析规则

1. 对每个已选帖子，调用 `image-analysis` skill 分析图片：
   - 执行：`python skills/image-analysis/scripts/analyze.py --post-id <id> --workspace <workspace_data_root>`
   - 注意：需要在 `skills/image-analysis/` 目录下执行，或使用绝对路径
2. 将每个帖子的图片分析结果整合到：
   - `image_patterns`：提取共性图片特征
   - `image_quality_notes`：整体图片质量评价
3. 若帖子无图片（返回 error），跳过该帖的图片分析
4. 图片分析结果文本不应直接复制，应提炼成结构化要点

## 写回约束

- `updated_at` 使用当前时间的 ISO 字符串
- `source_post_ids` 只写本轮实际消费的已选帖子 id
- `title_patterns`、`body_patterns`、`keywords`、`image_patterns` 都应是数组
- 不要把原始帖子全文或图片分析全文直接塞进结果文件
