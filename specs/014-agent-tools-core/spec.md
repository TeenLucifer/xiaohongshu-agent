# 014 Agent Tools Core

## 背景

主 agent runtime 需要一组稳定、受限、可测试的内置工具。首版工具层整体行为贴近 nanobot，但在 `exec` 的命令权限上收得更严。

## 目标

- 建立 `Tool` 基类和 `ToolRegistry`
- 提供完整的文件系统工具集
- 提供受限的 shell `exec` 工具
- 固定文件系统权限边界
- 固定 `exec` 的安全护栏、allowlist 和超时参数

## 非目标

- 浏览器内置工具
- web search / web fetch
- MCP / cron / spawn / message
- GitHub skill 安装

## 用户故事

- 作为 agent runtime，我希望有一组默认可用且边界清晰的内置工具。
- 作为开发者，我希望 tools 层尽量贴近 nanobot，减少重新发明。
- 作为运维者，我希望 `exec` 的命令权限比 nanobot 默认更严格。

## 输入输出

- 输入：tool 名称、参数、当前工作目录
- 输出：工具执行结果或清晰错误

## 约束

- `ToolsRegistry` 只注册首版必需工具：
  - `read_file`
  - `write_file`
  - `edit_file`
  - `list_dir`
  - `exec`
- `shell` 是能力类别，具体 tool 名为 `exec`
- 文件系统工具拆分与 `nanobot` 一致，不做聚合型 `file_system` 单工具
- 文件系统参数模型完全贴 `nanobot`：
  - `allowed_dir = session.workspace_path`
  - `extra_allowed_dirs = [project_root/skills, skill_dir, temp_dir]`
- 路径解析、越界判断、allowed/extra allowed 语义与 `nanobot` 一致
- `read_file` 同时支持文本与图片读取
- `write_file` 同时支持文本与 JSON 文件写入
- `edit_file` 保留 `nanobot` 风格的模糊匹配/去空白匹配/fallback 替换能力
- `exec` 参数与行为整体贴 `nanobot`：
  - 默认 `timeout = 60s`
  - 最大 timeout 上限 `600s`
  - 支持 `working_dir`
  - 输出包含 `stdout / stderr / exit code`
  - 超长输出采用 head+tail 截断
  - 超时 kill 进程并返回错误文本
- `exec` 的权限控制采用：
  - 命令前缀 allowlist
  - deny guard
  - 可选 `restrict_to_workspace`
- deny guard 至少拦截：
  - `rm -rf` / `rm -r`
  - `del /f` / `del /q`
  - `rmdir /s`
  - `format`
  - `mkfs` / `diskpart`
  - `dd if=`
  - 写盘到 `/dev/sd*`
  - `shutdown` / `reboot` / `poweroff`
  - fork bomb
- `exec` 保留 nanobot 风格的 internal/private URL 拦截与 workspace 越界检测
- `working_dir` 是首版唯一受支持的目录切换机制
- 首版不支持通过 `cd` 切目录
- 首版不鼓励使用 `&&` 进行 shell 串联
- 首版默认允许的命令前缀固定为：
  - `pwd`
  - `python`
  - `python3`
  - `node`
  - `ffmpeg`
  - `jq`
  - `unzip`
  - `playwright`
  - `python -m playwright`
  - `python3 -m playwright`
  - `uv run python`
  - `uv run python3`
  - `uv run node`
  - `npx playwright`
- 包装前缀只放行特定组合，不放开任意 `uv run ...` 或 `npx ...`
- 默认不放行：
  - `cd`
  - `ls`
  - `cat`
  - `git`
  - `npm install`
  - `pip install`
  - 依赖 `&&` 串联的 shell 组合写法
  - 任意非 allowlist 命令前缀
  - 任意破坏性命令
- 目录查看继续优先使用 `list_dir`
- 文件读取继续优先使用 `read_file`
- 需要在某个目录中执行命令时，应通过 `exec.command + exec.working_dir` 组合完成，而不是把目录切换写进 `command`
- runtime 默认会将项目根目录 `skills/` 注入工具执行上下文，使 builtin skills 的 `SKILL.md`、脚本和资源文件可直接访问
- runtime 应通过 system prompt 告知模型这些默认可访问目录与命令约束，而不是依赖 harness 或 user prompt 重复注入

## 验收标准

- `ToolRegistry` 可注册、查询和执行全部默认工具
- 文件系统工具只能访问 `allowed_dir` 与 `extra_allowed_dirs`
- 默认工具上下文会包含项目根目录 `skills/`
- `read_file` 可读取文本和图片
- `write_file` 可写入文本，也可在传入 `dict/list` 时自动序列化为 JSON 文件
- `edit_file` 的模糊匹配替换生效
- `exec` 的默认 timeout、最大 timeout 与输出截断行为符合约束
- `pwd` 可作为最小诊断命令执行
- `exec.working_dir` 可作为唯一目录切换机制正常工作
- 非 allowlist 命令前缀被拒绝
- `cd` 与依赖 `&&` 的命令写法被拒绝
- `uv run` / `npx` 仅特定组合可通过
- deny guard 危险命令被拦截
- 参数校验和错误返回清晰可测
