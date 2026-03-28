# 015 Agent Skills Loader

## 背景

主 agent 不重新设计 skill 协议，而是直接兼容 nanobot 的 skill 组织和加载方式。`015` 的实现以 `nanobot/agent/skills.py` 为基线，优先采用“移植 + 轻适配”的方式，而不是重新设计一套新的 skills loader。

## 目标

- 扫描 builtin skills 和 workspace skills
- 识别 `skills/<skill-name>/SKILL.md`
- 支持父 skill 与子 skills 同时发现
- 解析 `SKILL.md` frontmatter
- 生成 skills summary
- 支持 `always skills`
- 支持 `load_skills_for_context(...)`
- 加载指定 skill 的正文内容
- 检查 skill 的依赖要求

## 非目标

- GitHub 安装器
- skill 市场
- skill 执行脚本本身
- 自定义 manifest 协议

## 用户故事

- 作为主 agent，我希望像 nanobot 一样加载已有 skills，而不是重新设计一套 skill 格式。
- 作为实现者，我希望能明确知道某个 skill 是否可用、在哪里、需要什么依赖。
- 作为维护者，我希望该 loader 主要复用 nanobot 的成熟行为，只在路径、类型与 runtime 集成点上做轻适配。

## 输入输出

- 输入：builtin skills 目录、workspace skills 目录、skill 名称
- 输出：skill 列表、skills summary、指定 skill 的正文和元数据

## 约束

- `015` 以 `nanobot/agent/skills.py` 为实现基线，优先移植既有行为，仅做本地轻适配
- skill 协议直接兼容 nanobot
- skill 主入口固定为 `SKILL.md`
- 元数据来自 `SKILL.md` frontmatter
- frontmatter 解析参考 `openclaw` 的实现思路：
  - 正确支持 YAML frontmatter 与多行字段
  - `metadata` 字段如果是 JSON / JSON5，则继续解析 `nanobot` / `openclaw` 子字段
  - 不引入新的 `manifest.json`
- 需要支持 requirement 检查：
  - `bins`
  - `env`
- 需要支持 builtin 与 workspace skill 共存
- 扫描优先级贴 `nanobot`：
  - 先扫描 `workspace skills`
  - 再扫描 `builtin skills`
  - 同名 skill 时 `workspace` 覆盖 `builtin`
- 扫描方式采用“容器递归”：
  - 根目录继续识别 `skills/<skill-name>/SKILL.md`
  - 对每个已发现的 skill 目录，只沿其子目录中的 `skills/` 容器继续递归发现
  - 不做 openclaw 式全量目录递归
- 父 skill 与子 skills 需要同时暴露到 skills 列表和 summary 中
- 递归扫描时需要跳过噪音目录：
  - `.git`
  - `node_modules`
  - `__pycache__`
  - 隐藏目录
- 同源内的同名 skill 冲突处理保持简单：
  - 按稳定遍历顺序先到先得
  - 不新增路径命名空间
- `list_skills(filter_unavailable=True)` 默认过滤掉依赖不满足的 skill
- `build_skills_summary()` 必须列出全部 skills，包括不可用 skill，并标记可用性与缺失依赖
- `skills summary` 格式贴 `nanobot`，使用 XML-like 结构：
  - `<skills>`
  - `<skill available="true|false">`
  - `<name>`
  - `<description>`
  - `<location>`
  - 可选 `<requires>`
- 注入 skills summary 时必须明确告诉模型：
  - skills summary 只提供概览
  - 如需使用某个 skill，应先读取对应 `SKILL.md`
- 需要支持 `get_always_skills()`
  - 只返回依赖满足且被标记为 `always=true` 的 skill
- `ContextBuilder` 需要在 memory 之后、skills summary 之前注入 `always skills`
- 需要支持 `load_skill(name)`
  - 返回原始 `SKILL.md` 内容
- 需要支持 `load_skills_for_context(names)`
  - 去掉 frontmatter 后拼接为上下文块
- 需要对 nanobot 原始实现做的本地适配仅限于：
  - builtin/workspace 路径来源
  - 与本项目 runtime / `ContextBuilder` 的集成点
  - 返回类型与 schema 包装
- 不扩展新的 requirement 类型
- 不处理 skill 安装、下载和市场逻辑

## 验收标准

- 能按 nanobot 的优先级扫描 builtin 与 workspace skills
- 同名 skill 时 workspace 版本覆盖 builtin 版本
- 能在根目录 skill 之外，继续发现 `skills/` 容器中的子 skills
- 父 skill 与子 skills 会同时出现在 skills 列表和 summary 中
- 不会误扫 `scripts/`、`assets/` 或其他非 `skills/` 容器目录
- 能区分可用与不可用 skills
- 能生成 XML-like 的 skills summary
- skills summary 中的 `description` 能正确反映 `SKILL.md` 的真实描述，而不是 YAML 占位符
- skills summary 中会保留不可用 skill，并附缺失依赖信息
- 能识别并返回 `always skills`
- 能加载指定 skill 的完整内容
- 能加载去 frontmatter 后的上下文 skill 内容
- 能读取 frontmatter 中的名称、描述和 metadata
