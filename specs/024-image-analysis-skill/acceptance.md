# 024 Image Analysis Skill - Acceptance

## 功能验收

- [ ] `skills/image-analysis/SKILL.md` 存在且格式正确
- [ ] `skills/image-analysis/scripts/analyze.py` 可执行
- [ ] 调用 `python analyze.py --post-id xxx --workspace xxx` 返回分析结果
- [ ] 无图片时返回提示而非报错
- [ ] agent 可通过 skills loader 识别此 skill

## 集成验收

- [ ] pattern-summary 可调用 image-analysis
- [ ] 分析结果可整合到 pattern_summary.json 的 image_patterns 字段

## 输出格式验收

返回结构包含：
- [ ] `post_id` 字段
- [ ] `analysis` 文本字段
- [ ] `image_count` 数量字段
- [ ] `key_observations` 关键观察点列表