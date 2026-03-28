# 015 Agent Skills Loader Tasks

## 当前任务分组

- [x] `015-A`：建立 skills 扫描器
  以 nanobot 的扫描逻辑为基线，扫描 builtin skills 和 workspace skills 目录，并实现 workspace 覆盖 builtin。
- [x] `015-B`：实现 `SKILL.md` 解析
  读取 frontmatter 和正文内容，保留 nanobot 风格的轻量 key/value 解析与 `metadata` JSON 二次解析。
- [x] `015-C`：实现 requirement 检查
  校验 `bins` 与 `env` 依赖，并提供缺失依赖描述。
- [x] `015-D`：生成 skills summary
  按 nanobot 风格生成 XML-like skills summary，并保留不可用 skill 的可见性。
- [x] `015-E`：实现指定 skill 加载
  按名称加载 skill 的完整正文和元数据。
- [x] `015-F`：实现 `always skills`
  支持识别 `always=true` 的 skill，并返回依赖满足的 always skills 集合。
- [x] `015-G`：实现 `load_skills_for_context(...)`
  去除 frontmatter 后拼接指定 skill 正文，用于 `ContextBuilder` 注入。
- [x] `015-H`：完成本地轻适配
  仅适配路径来源、类型/schema 与 runtime 集成点，不重写 nanobot 的核心行为。

## 测试与验收

- [x] skills 扫描测试
- [x] workspace 覆盖 builtin 测试
- [x] frontmatter 解析测试
- [x] requirement 检查测试
- [x] 缺失依赖描述测试
- [x] skills summary 生成测试
- [x] 不可用 skill 仍出现在 summary 中的测试
- [x] `always skills` 识别测试
- [x] `load_skills_for_context(...)` 去 frontmatter 测试
- [x] 指定 skill 加载测试

## 实现收口

- [x] skills loader 已落地
- [x] skill 元数据读取已落地
- [x] nanobot 行为已完成移植并做本地轻适配
- [x] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成

## 备注

- 当前不处理 skill 安装与远程下载。
- 当前不验证 skill 脚本本身是否可运行。
