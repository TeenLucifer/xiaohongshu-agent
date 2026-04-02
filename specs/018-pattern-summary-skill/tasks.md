# 018 Pattern Summary Skill Tasks

## 当前任务分组

- [x] `018-A`：新增根级 `pattern-summary` skill 文档
- [x] `018-B`：固定输入为 `selected_posts.json + posts/<post_id>/post.json`
- [x] `018-C`：固定输出为 `workspace/pattern_summary.json`
- [x] `018-D`：接入右侧“总结”按钮，按钮复用现有 run 链路
- [x] `018-E`：接通 `context` 对真实总结文件的读取
- [x] `018-F`：将总结展示并入搜索结果区
  总结按钮和结果展示已并入搜索结果区下方，不再占据独立 section。

## 测试与验收

- [x] 右侧“总结”按钮展示测试通过
- [x] `pattern_summary` 真实读取测试通过
- [x] 无已选帖子时失败提示规则已写入 skill 文档

## 备注

- 第一版不新增脚本，不做多版本总结。
