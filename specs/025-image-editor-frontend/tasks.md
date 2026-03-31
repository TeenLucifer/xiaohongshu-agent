# 025 Image Editor Frontend - Tasks

## Phase 1: 类型定义

- [ ] 更新 `web/src/types/workspace.ts`
  - [ ] 添加 MaterialImage 接口
  - [ ] 添加 EditorImage 接口

## Phase 2: 组件实现

- [ ] 创建 `web/src/components/ImageEditorSection.tsx`
  - [ ] 实现素材图片网格
  - [ ] 实现编辑区图片网格
  - [ ] 实现拖拽功能
  - [ ] 实现编号显示
  - [ ] 实现移除功能

## Phase 3: 页面集成

- [ ] 更新 `web/src/app/TopicWorkspacePage.tsx`
  - [ ] 收集所有候选帖子的图片
  - [ ] 维护编辑区图片状态
  - [ ] 传递数据给 ImageEditorSection

## Phase 4: 后端集成

- [ ] 更新 `src/backend/topic_truth_models.py`
  - [ ] 添加 EditorImageRecord 模型
  - [ ] 添加 ImageEditorDocument 模型

- [ ] 更新 `src/backend/topic_truth_store.py`
  - [ ] 添加 read_editor_images 方法
  - [ ] 添加 write_editor_images 方法

- [ ] 更新 `src/backend/schemas.py`
  - [ ] 添加 EditorImageResponse schema

- [ ] 更新 `src/backend/service.py`
  - [ ] 添加 get_editor_images 方法
  - [ ] 添加 update_editor_images 方法

- [ ] 更新 `src/backend/app.py`
  - [ ] 添加 GET /api/topics/{topic_id}/editor-images
  - [ ] 添加 PUT /api/topics/{topic_id}/editor-images

## Phase 5: 前端 API 集成

- [ ] 更新 `web/src/lib/api.ts`
  - [ ] 添加 getEditorImages 函数
  - [ ] 添加 updateEditorImages 函数