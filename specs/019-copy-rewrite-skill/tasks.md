# 019 Copy Rewrite Skill Tasks

## 当前任务分组

- [x] `019-A`：新增根级 `copy-rewrite` skill 文档
- [x] `019-B`：固定输入为 `selected_posts.json + posts/<post_id>/post.json + pattern_summary.json`
- [x] `019-C`：固定输出为 `workspace/copy_draft.json`
- [x] `019-D`：接入右侧“文案”按钮，按钮复用现有 run 链路
- [x] `019-E`：接通 `context` 对真实文案文件的读取

## 测试与验收

- [x] 右侧“文案”按钮展示测试通过
- [x] `copy_draft` 真实读取测试通过
- [x] 缺少总结文件时失败提示规则已写入 skill 文档

## 备注

- 第一版不新增脚本，不做多版本文案。
