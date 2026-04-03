# 021 Topic Truth Store Acceptance

1. `workspace/posts/` 能被正确列举并组装为搜索结果
2. `selected_posts.json` 不再参与 `context` 组装
3. 删除帖子接口会同步删除 `workspace/posts/<post_id>/`
4. 删除帖子后，引用该帖的编辑区图片一并移除
5. 删除帖子不会自动清空已有总结或文案
6. `pattern_summary.json`、`copy_draft.json`、`editor_images.json`、`image_results.json` 继续正常读写
