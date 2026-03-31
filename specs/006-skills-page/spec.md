# 006 Skills Page

## 背景

当前左侧导航里已经有 `Skills` 入口，但仍是占位按钮，前端也没有统一查看所有已加载 skills 的页面。与此同时，后端已经具备 `015-agent-skills-loader` 的真实扫描与加载能力，适合补一个只读 skills 页面，把当前运行上下文里可见的 skills 展示出来。

## 目标

- 新增独立的 `/skills` 页面
- 一页展示全部已加载 skills
- 同时展示 builtin、workspace 和子 skills
- 明确展示 skill 是否可用，以及缺失依赖信息
- 点击某个 skill 后，通过弹窗查看详细信息
- 详情第一版展示：
  - 名称
  - 描述
  - 来源位置
  - 可用状态
  - 缺失依赖
  - `SKILL.md` 去 frontmatter 后的正文摘要
- Skills 详情弹窗中的正文摘要支持 GFM 基础 Markdown 显示

## 非目标

- skill 安装、启用、禁用、执行
- 搜索、筛选、排序、分组
- 完整 markdown 文档阅读器
- 原始 HTML 渲染
- 代码高亮
- 编辑 `SKILL.md`

## 用户故事

- 作为运营人员，我希望能快速看到当前系统有哪些 skills 可用，而不必去读源码或 trace。
- 作为开发者，我希望能直接看到某个 skill 的来源位置、依赖状态和正文摘要，便于调试和联调。
- 作为使用者，我希望技能正文中的标题、列表、代码块和链接能按 Markdown 结构显示，而不是纯文本堆在一起。
- 作为使用者，我希望从左侧 `Skills` 入口进入一个独立页面，而不是在工作台里打开临时弹层。

## 输入输出

- 输入：
  - `015-agent-skills-loader` 的 skills 扫描结果
  - 当前 `data/sessions/*/skills` 中的 workspace skills
- 输出：
  - `/skills` 页面
  - `GET /api/skills` 只读接口

## 约束

- 前端路由新增：
  - `/skills`
- 左侧导航中的 `Skills` 必须变为真实页面入口
- Skills 页面与首页 `/`、话题工作台 `/topics/:topicId` 并列
- `GET /api/skills` 返回全部 skills，不过滤不可用项
- 后端返回字段至少包括：
  - `name`
  - `description`
  - `source`
  - `location`
  - `available`
  - `requires`
  - `content_summary`
- `content_summary` 来自 `SKILL.md` 去 frontmatter 后的正文摘要
- `content_summary` 在前端按 GFM 基础 Markdown 只读渲染
- Skills 详情不支持原始 HTML
- 第一版不单独新增详情接口，列表接口返回弹窗所需信息即可
- workspace skills 的聚合规则为：
  - 先取 builtin skills
  - 再遍历现有 session 目录中的 workspace skills
  - 只追加 `source == "workspace"` 的记录
  - 按 `path` 去重

## 验收标准

- 点击左侧 `Skills` 能进入独立的 `/skills` 页面
- Skills 页面能展示全部 skills
- builtin、workspace、父 skill、子 skill 都可出现在列表中
- 不可用 skill 不会被过滤掉，并会显示缺失依赖信息
- 点击 skill 后会打开弹窗
- 弹窗能显示元数据和正文摘要
- 弹窗中的正文摘要 Markdown 结构可正确显示
- Skills 页面不需要搜索、筛选、排序也能完成第一版使用目标
- 现有首页、话题工作台和左侧导航行为不回归
