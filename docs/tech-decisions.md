# 技术决策

## 当前工程基线

- Python `3.11+`
- `uv` 负责依赖和命令执行
- `ruff` 负责 lint 与格式检查
- `pyright` 负责静态类型检查
- `pytest` 负责测试

## 已确认的核心决策

### 1. 主体形态

- 采用一个主 agent runtime
- 不做多个对等 agent
- 产品层围绕 `topic`
- runtime 层围绕 `session`

### 2. Skill 协议

- 完全兼容 nanobot 风格 `SKILL.md`
- skills loader 以 `nanobot/agent/skills.py` 为实现基线
- 支持 `always skills`
- 不自定义 `manifest.json`

### 3. Session / History

- `session_id` 使用 `uuid4`
- session history 使用 `jsonl`
- 第一行 metadata，后续每行 message
- 内存维护完整 session，每次 save 重写文件

### 4. Context / Memory

- 长期记忆采用：
  - `MEMORY.md`
  - `HISTORY.md`
- 记忆治理贴 nanobot
- 使用 `last_consolidated` 作为沉淀游标
- 不引入向量数据库

### 5. Loop

- loop 停止模型贴 nanobot
- `max_iterations = 20`
- 不做 run-level timeout
- 不做结构化 run 状态模型
- tool 普通失败转成结果回灌，不直接打断 loop

### 6. Tools

- 首版只内置：
  - 文件系统工具
  - `exec`
- 浏览器能力不内置
- 浏览器/CDP 由 skills 自己通过脚本和 `exec` 使用

### 7. exec 权限策略

- `exec` 采用：
  - allowlist
  - deny guard
- 默认 tool timeout `60s`
- 最大 timeout `600s`
- 只放行固定命令前缀和指定包装组合

## 为什么这样选

### 单主 agent

- 降低编排复杂度
- 更适合 session 级长会话
- 与当前运营工作台形态更匹配

### nanobot 风格 skills

- 已有成熟参考实现
- 便于后续复用现有 `xiaohongshu-skills`
- 减少重复设计协议的成本

### session + memory 分层

- 短期历史和长期记忆边界更清晰
- 长会话不会无限增长
- 后续便于持续总结与复盘

### filesystem + exec 极简工具层

- 先把 runtime 核心跑通
- 避免过早引入浏览器工具和重型能力层
- skill 自带脚本更适合平台差异化能力

## 当前未实现但已定方向

- backend glue 层
- 文件化真相层
- skill 安装与远程同步
- 前后端真实联调链路

这些能力后续应继续通过 `specs/` 细化，而不是直接跳过规格进入实现。
