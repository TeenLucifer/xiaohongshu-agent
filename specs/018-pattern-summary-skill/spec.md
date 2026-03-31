# 018 Pattern Summary Skill

## 背景

当前工作区已经具备：

- `workspace/posts/<post_id>/post.json` 帖子包
- `workspace/selected_posts.json` 已选帖子真相层
- `workspace/pattern_summary.json` 的稳定 schema

但“总结”仍缺少一个明确的生成能力边界。第一版不通过脚本或专门后端接口生成，而是通过一个 instruction-only skill，让 agent 直接读取当前 workspace 中的已选帖子并写回结构化总结文件。

## 目标

- 提供一个根级 `pattern-summary` skill
- 让 agent 能基于当前 `selected_posts.json` 对应帖子生成结构化总结
- 将结果写回 `workspace/pattern_summary.json`
- 支持主栏对话触发与右侧“总结”按钮触发

## 非目标

- 单独脚本或 CLI
- 多版本总结管理
- 数据库或搜索索引
- 直接生成文案

## 用户故事

- 作为运营人员，我希望选好帖子后，可以一键得到结构化总结，而不用手写提示词。
- 作为 agent，我希望有一个明确 skill 告诉我该读哪些文件、写哪个结果文件。

## 输入输出

- 输入：
  - `Workspace Data Root`
  - `workspace/selected_posts.json`
  - `workspace/posts/<post_id>/post.json`
  - `workspace/posts/<post_id>/assets/image-*.jpg`（通过 `image-analysis` skill）
- 输出：
  - `workspace/pattern_summary.json`
  - 一条主栏 final answer，总结本轮写入结果

## 约束

- skill 放在项目根 `skills/` 下，与 `xiaohongshu-skills` 并列
- skill 不新增脚本，只使用现有文件工具
- 只消费 `selected_posts.json` 中的帖子，不直接消费全部帖子包
- 总结时必须调用 `image-analysis` skill 分析每篇已选帖子的图片
- 若帖子无图片，跳过图片分析，继续处理文本
- 若没有已选帖子：
  - 不写 `pattern_summary.json`
  - 明确提示用户先加入已选帖子
- 写回结果必须遵循 `PatternSummaryRecord`，包含 `image_patterns` 和 `image_quality_notes` 字段
- 右侧”总结”按钮本质上只是代用户发送固定指令，不新增第二套后端动作

## 输出字段

`pattern_summary.json` 内容至少包含：

- `title_patterns`：标题模式列表
- `body_patterns`：正文模式列表
- `keywords`：关键词列表
- `image_patterns`：图片共性特征列表
- `image_quality_notes`：整体图片质量评价
- `summary_text`：总结文本（可选）
- `source_post_ids`：来源帖子 ID 列表
- `updated_at`：更新时间

## 验收标准

- agent 能识别并加载 `pattern-summary` skill
- 基于已选帖子能写出合法的 `pattern_summary.json`
- 右侧“总结”区可通过按钮触发一次 run
- run 完成后右侧工作区能显示真实总结结果
- 无已选帖子时不会写文件，并给出明确失败提示
