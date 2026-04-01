# 025 Image Generation Skill Tasks

## 文档与边界

- [x] `025-A`：明确图片生成主 spec
- [x] `025-B`：明确与 `003/004/007/011/020/021` 的联动边界

## 后端与真相层

- [x] `025-C`：补 `editor_images.json` 真相层与 GET/PUT API
- [x] `025-D`：将 `image_results.json` 改为单列表真实读取/写入
- [x] `025-E`：将生成图片文件稳定写入 `workspace/generated_images/`
- [x] `025-F`：在消息 DTO 中补图片附件元数据

## Skill 与执行

- [x] `025-G`：新增根级 `image-generation` skill
- [x] `025-H`：新增图片生成脚本并接入现有模型配置
- [x] `025-I`：在 runtime prompt 中补图片生成调用规则
- [x] `025-Q`：将图片生成脚本替换为 Gemini 多参考图 base64 输入实现

## 前端

- [x] `025-J`：右侧“图片”section 内部改为“编辑区在上、结果区在下”
- [x] `025-K`：生成结果支持放大、删除、拖拽进入编辑区
- [x] `025-L`：final answer 下展示 1 张代表缩略图
- [x] `025-M`：editor images 改为真实持久化，不再只存在本地状态

## 测试

- [x] `025-N`：后端 truth store / context / message DTO 测试通过
- [x] `025-O`：skill / script 最小编译校验通过
- [x] `025-P`：前端图片 section 与聊天缩略图测试通过
