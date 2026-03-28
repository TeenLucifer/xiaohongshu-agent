# 015 Agent Skills Loader Tasks

## 当前状态

- [x] `015-agent-skills-loader` 已完成，当前处于维护与联调阶段。

## 已完成里程碑

- [x] 建立 builtin / workspace skills 扫描与覆盖规则，固定 workspace 优先级高于 builtin。
- [x] 完成 `SKILL.md` 解析，支持参考 openclaw 的 YAML frontmatter、多行 description 与 `metadata` 二次解析。
- [x] 完成 requirement 检查、`always skills`、指定 skill 加载与 `load_skills_for_context(...)`。
- [x] 建立 XML-like skills summary，保留 `name + description + location`，并提示模型使用前先读取 `SKILL.md`。
- [x] 实现容器递归扫描、父子 skill 同时暴露、噪音目录跳过与同源内先到先得规则。

## 当前待办

- [ ] 当前无进行中的 `015` 子任务；后续如有 skill 协议或扫描规则调整，再在此补充。

## 备注

- 详细验收与测试要求以下列文档为准：`acceptance.md`
