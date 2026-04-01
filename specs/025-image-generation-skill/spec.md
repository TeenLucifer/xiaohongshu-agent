# 025 Image Generation Skill

## 背景

当前仓库已经有：

- 帖子包下载与图片分析能力
- 右侧“创作”tab 下的图片编辑区
- 图片大图预览能力

但还没有“基于编辑区参考图 + 用户提示词”生成真实图片，并将结果回写到当前 workspace 的完整闭环。

## 目标

- 新增一个根级 `image-generation` skill
- 支持 agent 读取当前 workspace 中的编辑区图片与用户提示词生成图片
- 将生成结果稳定写入当前 session 的 workspace
- 让中间对话与右侧图片区都能消费同一批真实图片结果

## 非目标

- 纯文生图
- 独立的图片生成按钮
- 复杂画布编辑
- 图片精修、多轮局部重绘
- 物理删除历史图片文件

## 用户故事

- 作为运营人员，我希望把参考图拖进编辑区后，直接在对话里描述“参考 1 号图的风格，把 2 号图主体替换到 1 号图中”，然后得到新的图片结果。
- 作为运营人员，我希望本轮生成出的图片能立即出现在聊天结果里，同时也能在右侧图片区继续查看、放大、删除或加入编辑区。
- 作为实现者，我希望图片生成结果只有一套 workspace 真相层，而不是聊天区和右侧各自维护一份。

## 输入输出

- 输入：
  - `Workspace Data Root`
  - `editor_images.json`
  - 用户当前图片生成提示词
- 输出：
  - `workspace/generated_images/<image_id>.png`
  - `workspace/image_results.json`
  - final answer 下的单张代表缩略图

## 约束

- 第一版只通过主栏对话触发，不新增右侧“生成图片”按钮
- 第一版只支持“编辑区参考图 + 用户提示词”生成，不支持纯文生图
- 若编辑区为空，不生成图片，需明确提示用户先拖入参考图
- 若用户提示词引用了不存在的“X 号图”，不生成图片，需明确提示用户编号无效
- 第一版直接将编辑区原始参考图转成 base64 图片输入，不再先构建拼板图
- 第一版图片编辑失败时直接报错，不回退纯文生图
- 生成结果真相层固定为当前 session 的 `workspace/`
- 右侧“创作”tab 下的“图片”section 内部拆成两块：
  - 上半部分：编辑区
  - 下半部分：生成结果展示区
- 生成结果展示区按单列表追加展示，不再按“文生图 / 图生图”分组
- 每张结果图都需要支持：
  - 点图放大
  - 右上角 `X` 删除
  - 拖拽到编辑区
- 聊天区 final answer 下只附 1 张代表缩略图
- 聊天缩略图和右侧结果区必须引用同一份 workspace 图片结果
- 删除结果区图片时，第一版只移除 `image_results.json` 中的索引，不强制删除底层文件

## 技能边界

### image-generation

职责：

- 读取 `Workspace Data Root/editor_images.json`
- 解析用户提示词中引用的编辑区编号
- 直接将原始参考图转成 base64 输入 Gemini 图片模型
- 将图片文件写入 `generated_images/`
- 将结果索引写回 `image_results.json`

不负责：

- 搜索帖子
- 维护已选帖子
- 直接修改前端状态
- 决定是否将结果加入编辑区
- 失败时退回纯文生图

## Workspace 真相层

第一版新增或推进以下对象：

- `workspace/editor_images.json`
- `workspace/generated_images/<image_id>.png`
- `workspace/image_results.json`

### editor_images.json

保存当前编辑区图片顺序与来源信息，供图片生成 skill 读取。

### image_results.json

改为单列表结构，每项至少包含：

- `id`
- `image_path`
- `alt`
- `prompt`
- `source_editor_image_ids`
- `created_at`

新结果始终追加到列表尾部。

## 前端展示

### 中间对话

- final answer 下展示 1 张代表图
- 代表图默认取本轮新生成结果的第一张
- 聊天区继续只展示 final answer，不展示额外图片过程日志

### 右侧创作 tab

图片 section 内部结构固定为：

1. 图片编辑区
2. 生成结果展示区

生成结果展示区视觉形态参考素材图区：

- 小图网格
- 结果追加在尾部
- 每张图右上角 `X`
- 缩略图尺寸与素材图区一致
- 每张图可拖拽到编辑区

## 与其他 feature 的关系

- `003-content-creation`
  - 定义聊天缩略图与右侧图片区的展示口径
- `004-conversation-timeline`
  - 定义 final answer 下的图片附件展示
- `007-image-editor-frontend`
  - 编辑区真实化并持久化到 `editor_images.json`
- `011-session-history-core`
  - session message 需支持图片附件元数据
- `020-backend-glue-minimal`
  - 补 editor images 与图片结果相关 API
- `021-topic-truth-store`
  - 承接 `editor_images.json`、`image_results.json` 与生成图片文件

## 验收标准

- 有编辑区图片时，主栏图片生成请求能生成真实图片文件
- `workspace/generated_images/` 下能看到新图片
- `workspace/image_results.json` 追加写入新结果
- `GET /api/topics/{topic_id}/context` 能返回真实图片结果
- 右侧图片 section 下半部分能展示生成结果
- final answer 下能展示 1 张代表图
- 结果图支持放大、删除和拖拽到编辑区
- 编辑区为空或编号无效时，agent 明确失败，不写入结果
