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
9.1 准备一个使用 YAML 多行 `description: |` 的 skill
9.2 确认读取出的 description 为真实多行描述，而不是字面量 `|`
10. 检查某个 skill 的 requirement
11. 确认可判断是否缺少命令或环境变量
12. 生成 skills summary
13. 确认 summary 使用 XML-like 结构，并包含 `available` 状态、`name`、`description`、`location`
13.1 确认 summary 中明确提示：如需使用某个 skill，应先读取对应 `SKILL.md`
14. 准备一个依赖不满足的 skill
15. 确认该 skill 仍出现在 summary 中，并显示缺失依赖
16. 准备一个 `always=true` 的可用 skill
17. 确认该 skill 可被 `get_always_skills()` 识别
18. 按名称加载一个指定 skill
19. 确认返回完整正文内容
20. 通过 `load_skills_for_context(...)` 加载该 skill
21. 确认 frontmatter 已被去除，仅保留正文内容
22. 准备一个父 skill 目录，例如 `skills/xiaohongshu-skills/SKILL.md`
23. 在其子目录 `skills/xiaohongshu-skills/skills/` 下再准备多个子 skills
24. 重新扫描 skills 列表
25. 确认父 skill 与子 skills 会同时被发现
26. 生成 skills summary
27. 确认 summary 中同时包含父 skill 和各子 skills
28. 在父 skill 目录下额外准备 `scripts/`、`assets/` 等目录
29. 确认递归扫描不会误把这些目录中的文件识别成 skill
30. 在递归目录中加入 `.git`、`node_modules`、`__pycache__` 或隐藏目录
31. 确认这些噪音目录被跳过

## 自动化验收

- skills 扫描测试通过
- workspace 覆盖 builtin 测试通过
- frontmatter 解析测试通过
- 多行 YAML description 解析测试通过
- requirement 检查测试通过
- 缺失依赖描述测试通过
- skills summary 生成测试通过
- skills summary 使用说明测试通过
- 不可用 skill 仍出现在 summary 中的测试通过
- `always skills` 测试通过
- `load_skills_for_context(...)` 去 frontmatter 测试通过
- 指定 skill 加载测试通过
- 容器递归扫描测试通过
- 父子 skill 同时发现测试通过
- 非 `skills/` 容器目录不误扫测试通过
- 噪音目录跳过测试通过
- `xiaohongshu-skills` nested 结构回归测试通过

## 已知限制

- 当前不负责 skill 安装
- 当前不验证 skill 脚本本身是否可运行
- 当前主要以 nanobot 的 `skills.py` 为实现基线，但在扫描方式上扩展为“仅沿 `skills/` 容器递归”
- frontmatter 解析参考 openclaw 的实现思路，以正确支持 YAML 多行字段
