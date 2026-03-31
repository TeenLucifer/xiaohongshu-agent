# 019 Copy Rewrite Skill Acceptance

## 手工验收

1. 进入一个已有已选帖子和总结结果的 topic 工作台
2. 展开右侧“文案”区
3. 确认存在“生成文案”或“重新生成文案”按钮
4. 点击按钮
5. 确认主栏出现一条 user 请求和一条 agent final answer
6. 确认当前 session 的 `workspace/copy_draft.json` 被写入
7. 确认右侧“文案”区显示真实文案结果
8. 在缺少总结结果的 topic 中重复操作
9. 确认 agent 明确提示先生成总结，且不写结果文件

## 自动化验收

- skill 文档发现测试通过
- 右侧“文案”按钮渲染测试通过
- `context` 返回真实 `copy_draft` 测试通过

## 已知限制

- 当前不做多版本文案
- 当前不提供专门按钮接口，按钮仅复用现有 run 链路
