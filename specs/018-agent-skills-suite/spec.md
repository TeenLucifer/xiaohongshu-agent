# 018 Agent Skills Suite

## 背景

业务 skill 统一收录在同一组 spec 中。总结、文案、图片分析、图片生成、选区润色都围绕当前 workspace 运行。

## 当前口径

- `pattern-summary`
  - 读取当前全部剩余帖子
  - 写入 `pattern_summary.json`
- `copy-rewrite`
  - 读取当前全部剩余帖子和 `pattern_summary.json`
  - 写入 `copy_draft.json`
- `image-analysis`
  - 读取图片分析 skill 自己的 `config.json`
- `image-generation`
  - 读取图片生成 skill 自己的 `config.json`
- `selection-polish`
  - 读取整篇文案上下文，但只返回选区替换文本

## 验收标准

- summary/copy 类 skill 不再依赖 `selected_posts.json`
- 图片类 skill 只读取各自目录下的 `config.json`
- skill 文档与当前 workspace 真相层口径一致
