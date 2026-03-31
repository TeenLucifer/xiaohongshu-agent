# 024 Image Analysis Skill

## 背景

当前工作区已经具备：

- `workspace/posts/<post_id>/post.json` 帖子包
- `workspace/posts/<post_id>/assets/image-*.jpg` 图片资源
- 硅基流动（SiliconCloud）视觉 API 可用

但"帖子总结"缺少对图片内容的视觉分析能力。运营人员需要了解：
- 图片的构图、色彩等视觉特征
- 图片为什么能吸引流量
- 图片可能存在的问题

## 目标

- 提供一个根级 `image-analysis` skill
- 让 agent 能调用视觉 API 分析帖子图片
- 返回结构化文本分析结果，供 pattern-summary 等 skill 消费

## 非目标

- 图片生成或编辑
- 图片质量评分算法（纯视觉模型分析）
- 图片标签/分类系统
- 单独后端 API

## 用户故事

- 作为运营人员，我希望总结帖子时能看到图片的视觉分析结果。
- 作为 agent，我希望有一个 skill 告诉我如何调用视觉 API 分析图片。
- 作为 pattern-summary skill，我希望能调用 image-analysis 获取图片分析结果。

## 输入输出

- 输入：
  - `Workspace Data Root`
  - `--post-id` 指定要分析的帖子
  - `workspace/posts/<post_id>/assets/image-*.jpg`
- 输出：
  - 结构化文本分析结果（包含 post_id、analysis、image_count、key_observations）

## 约束

- skill 放在项目根 `skills/` 下，与 `pattern-summary`、`copy-rewrite` 并列
- skill 通过脚本调用硅基流动视觉 API
- 使用 OpenAI 兼容的多模态消息格式
- 每篇帖子最多分析 5 张图片（token 预算控制）
- 若帖子无图片资源：
  - 返回明确提示"无图片可分析"
  - 不抛错，允许继续流程

## 执行链路

1. agent 识别 `image-analysis` skill
2. agent 执行：`python skills/image-analysis/scripts/analyze.py --post-id <id> --workspace <root>`
3. 脚本读取帖子图片，调用视觉 API
4. 脚本返回结构化分析文本
5. agent 将分析结果整合到后续流程

## 视觉分析内容

分析应覆盖：

- 构图特征：主体位置、层次感、对称性等
- 色彩特征：色调、饱和度、对比度等
- 内容特征：人物、产品、场景等
- 吸引力因素：可能的点击驱动点
- 问题点：模糊、水印、过度后期等

## 与现有 feature 的关系

- `018-pattern-summary-skill`
  - 在总结时调用 `image-analysis` 获取图片分析结果
  - 将结果整合到 `image_patterns` 和 `image_quality_notes`
- `019-copy-rewrite-skill`
  - 可在文案生成时参考图片风格
- `021-topic-truth-store`
  - 继续定义 `PostMediaAsset` 结构

## 验收标准

- agent 能识别并加载 `image-analysis` skill
- 脚本能正确读取帖子图片并调用视觉 API
- 返回结构化分析文本
- 无图片时返回明确提示而非报错
- pattern-summary 能调用此 skill 并整合结果