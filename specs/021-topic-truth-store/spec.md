# 021 Topic Truth Store

## 背景

工作区对象全部以当前 active session 的 workspace 作为真相层。搜索结果不再维护“已选帖子”第二套状态，当前剩余帖子本身就是后续流程输入。

## 目标

- 为 workspace 提供稳定文件化对象存储
- `candidatePosts` 直接由 `workspace/posts/` 组装
- 总结、文案、图片等对象独立读写
- 删除帖子时支持同步删除帖子包，并清理引用该帖的编辑区图片

## 真相对象

- `workspace/posts/<post_id>/post.json`
- `workspace/posts/<post_id>/raw.json`
- `workspace/posts/<post_id>/assets/...`
- `workspace/pattern_summary.json`
- `workspace/copy_draft.json`
- `workspace/editor_images.json`
- `workspace/image_results.json`
- `workspace/materials.json`
- `workspace/materials/...`

## 约束

- `selected_posts.json` 不再作为正式对象使用
- `candidatePosts` 只由当前全部剩余帖子包组装
- 删除帖子后：
  - 对应帖子包被彻底删除
  - 来源于该帖的编辑区图片一并移除
  - 已有总结和文案保留不动
- 图片上传使用独立真相层：
  - `materials.json` 保存本地上传图片记录
  - 上传图片文件落到 `workspace/materials/`
- 删除上传图片后：
  - 上传图片记录被移除
  - 若编辑区引用了该图片，则相应编辑区图片也一并移除

## 验收标准

- `context` 返回的搜索结果不再含 `selected/manualOrder`
- 删除帖子接口会真实删除帖子包
- 删除后 `candidatePosts` 与 `editor_images` 同步更新
- 总结、文案、图片结果的读写链路继续可用
- 图片上传记录的读写与删除链路继续可用
