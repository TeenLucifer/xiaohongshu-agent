# 015 Agent Skills Loader Acceptance

## 手工验收

1. 准备 builtin skills 目录
2. 准备 workspace skills 目录
3. 在目录中放入符合 nanobot 风格的 `SKILL.md`
4. 扫描 skills 列表
5. 确认可识别 builtin 和 workspace 两类 skills
6. 准备一个同名 builtin/workspace skill
7. 确认 workspace 版本覆盖 builtin 版本
8. 检查某个 skill 的 frontmatter
9. 确认可读取名称、描述和 metadata
10. 检查某个 skill 的 requirement
11. 确认可判断是否缺少命令或环境变量
12. 生成 skills summary
13. 确认 summary 使用 XML-like 结构，并包含 `available` 状态
14. 准备一个依赖不满足的 skill
15. 确认该 skill 仍出现在 summary 中，并显示缺失依赖
16. 准备一个 `always=true` 的可用 skill
17. 确认该 skill 可被 `get_always_skills()` 识别
18. 按名称加载一个指定 skill
19. 确认返回完整正文内容
20. 通过 `load_skills_for_context(...)` 加载该 skill
21. 确认 frontmatter 已被去除，仅保留正文内容

## 自动化验收

- skills 扫描测试通过
- workspace 覆盖 builtin 测试通过
- frontmatter 解析测试通过
- requirement 检查测试通过
- 缺失依赖描述测试通过
- skills summary 生成测试通过
- 不可用 skill 仍出现在 summary 中的测试通过
- `always skills` 测试通过
- `load_skills_for_context(...)` 去 frontmatter 测试通过
- 指定 skill 加载测试通过

## 已知限制

- 当前不负责 skill 安装
- 当前不验证 skill 脚本本身是否可运行
- 当前主要以 nanobot 的 `skills.py` 为实现基线，仅做路径、类型和 runtime 集成的轻适配
