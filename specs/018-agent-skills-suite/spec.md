# 018 Agent Skills Suite

## 背景

业务 skill 统一收录在同一组 spec 中。总结、文案、图片分析、图片生成、选区润色都围绕当前 workspace 运行。

## 当前口径

- `xhs-explore`
  - 作为底层内容发现 skill，负责搜索、详情查看与用户主页查看
  - 在回复中列出帖子结果时，默认附带原始小红书链接，优先使用 Markdown 标题链接
  - 原始链接默认应为基于 `feed_id + xsec_token` 构造的完整详情 URL，而不是裸 `explore/<id>` 链接
  - 小红书选题、对标与方向调研不再使用独立 skill；其简短原则由 runtime system prompt 定义，实际搜索与详情仍由 `xhs-explore` 承接
- `pattern-summary`
  - 读取当前全部剩余帖子
  - 写入 `pattern_summary.json`
- `copy-rewrite`
  - 读取当前全部剩余帖子和 `pattern_summary.json`
  - 写入 `copy_draft.json`
- `image-analysis`
  - 读取图片分析 skill 自己的 `config.json`
  - 可由设置页统一管理 `base_url / api_key / model`
- `image-generation`
  - 读取图片生成 skill 自己的 `config.json`
  - 可由设置页统一管理 `base_url / api_key / model`
- `selection-polish`
  - 读取整篇文案上下文，但只返回选区替换文本

## 验收标准

- `xhs-explore` 在搜索/调研回复中为帖子结果附带可点击原始链接，并默认使用完整详情 URL
- 小红书选题、对标与方向调研默认只搜索和分析，不默认下载、不落盘；只有用户明确要求下载时才进入下载链路
- summary/copy 类 skill 不再依赖 `selected_posts.json`
- 图片类 skill 只读取各自目录下的 `config.json`
- skill 文档与当前 workspace 真相层口径一致
