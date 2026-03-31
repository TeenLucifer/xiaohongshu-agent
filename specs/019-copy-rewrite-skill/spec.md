# 019 Copy Rewrite Skill

## 背景

当前工作区已经具备：

- `workspace/posts/<post_id>/post.json` 帖子包
- `workspace/selected_posts.json` 已选帖子真相层
- `workspace/pattern_summary.json` 总结真相层
- `workspace/copy_draft.json` 的稳定 schema

但“文案改写”仍缺少一个明确生成边界。第一版同样采用 instruction-only skill，让 agent 直接读取当前 workspace 中的已选帖子和总结文件，再写回结构化文案文件。

## 目标

- 提供一个根级 `copy-rewrite` skill
- 让 agent 基于已选帖子和总结结果生成文案
- 将结果写回 `workspace/copy_draft.json`
- 支持主栏对话触发与右侧“文案”按钮触发

## 非目标

- 单独脚本或 CLI
- 多版本文案管理
- 富文本编辑器持久化
- 图片生成

## 用户故事

- 作为运营人员，我希望在总结完成后，可以一键得到一版可编辑文案。
- 作为 agent，我希望有一个明确 skill 告诉我必须先读总结，再写文案文件。

## 输入输出

- 输入：
  - `Workspace Data Root`
  - `workspace/selected_posts.json`
  - `workspace/posts/<post_id>/post.json`
  - `workspace/pattern_summary.json`
- 输出：
  - `workspace/copy_draft.json`
  - 一条主栏 final answer，总结本轮写入结果

## 约束

- skill 放在项目根 `skills/` 下，与 `xiaohongshu-skills` 并列
- skill 不新增脚本，只使用现有文件工具
- 只消费 `selected_posts.json` 中的帖子
- 必须先读取 `pattern_summary.json`
- 若没有已选帖子：
  - 不写 `copy_draft.json`
  - 明确提示用户先加入已选帖子
- 若没有总结文件：
  - 不写 `copy_draft.json`
  - 明确提示用户先生成总结
- 写回结果必须遵循 `CopyDraftRecord`
- 右侧“文案”按钮本质上只是代用户发送固定指令，不新增第二套后端动作

## 验收标准

- agent 能识别并加载 `copy-rewrite` skill
- 基于已选帖子和总结文件能写出合法的 `copy_draft.json`
- 右侧“文案”区可通过按钮触发一次 run
- run 完成后右侧工作区能显示真实文案结果
- 缺少总结文件时不会写文件，并给出明确失败提示
