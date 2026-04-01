# 007 Image Editor Frontend - Tasks

## Phase 1: 类型定义

- [x] 更新 `web/src/types/workspace.ts`
  - [x] 添加 MaterialImage 接口
  - [x] 添加 EditorImage 接口

## Phase 2: 组件实现

- [x] 创建 `web/src/components/ImageEditorSection.tsx`
  - [x] 实现素材图片网格
  - [x] 实现编辑区图片网格
  - [x] 实现拖拽功能
  - [x] 实现编号显示
  - [x] 实现移除功能

## Phase 3: 页面集成

- [x] 更新 `web/src/app/TopicWorkspacePage.tsx`
  - [x] 收集所有候选帖子的图片
  - [x] 维护编辑区图片状态
  - [x] 传递数据给 ImageEditorSection

## Phase 4: 后端集成

- [x] 更新 `src/backend/topic_truth_models.py`
  - [x] 添加 EditorImageRecord 模型
  - [x] 添加 EditorImagesDocument 模型

- [x] 更新 `src/backend/topic_truth_store.py`
  - [x] 添加 read_editor_images 方法
  - [x] 添加 write_editor_images 方法

- [x] 更新 `src/backend/schemas.py`
  - [x] 添加 EditorImageResponse schema

- [x] 更新 `src/backend/service.py`
  - [x] 添加 get_editor_images 方法
  - [x] 添加 update_editor_images 方法

- [x] 更新 `src/backend/app.py`
  - [x] 添加 GET /api/topics/{topic_id}/editor-images
  - [x] 添加 PUT /api/topics/{topic_id}/editor-images

## Phase 5: 前端 API 集成

- [x] 更新 `web/src/lib/api.ts`
  - [x] 添加 getEditorImages 函数
  - [x] 添加 updateEditorImages 函数
