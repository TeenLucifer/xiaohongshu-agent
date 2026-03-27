# 014 Agent Tools Core Tasks

## 当前任务分组

- [ ] `014-A`：建立 `Tool` 基类和 `ToolRegistry`
  对齐 nanobot 的最小工具抽象和注册方式。
- [ ] `014-B`：实现文件系统工具集
  完成 `read_file`、`write_file`、`edit_file`、`list_dir`，并保留 `read_file` 图片支持与 `edit_file` 模糊匹配能力。
- [ ] `014-C`：固定文件系统权限边界
  采用 nanobot 风格的 `allowed_dir + extra_allowed_dirs` 模型，将路径限制在 session 工作目录、临时目录和 skill 目录内。
- [ ] `014-D`：实现 `exec` 工具
  完成工作目录、命令前缀 allowlist、deny guard、internal/private URL 拦截、workspace 越界检测和 `60s` 默认超时。
- [ ] `014-E`：固定 `exec` 的默认 allowlist
  写死首版允许的裸命令与包装命令前缀，并拒绝任意非白名单命令。
- [ ] `014-F`：补齐工具层参数校验与错误表达
  统一返回格式、超时行为、输出截断和执行错误处理。

## 测试与验收

- [ ] `ToolRegistry` 注册与执行测试
- [ ] 文件系统工具读写编辑列举测试
- [ ] `read_file` 图片读取测试
- [ ] `edit_file` 模糊匹配替换测试
- [ ] 文件系统越界拦截测试
- [ ] shell 非 allowlist 命令拦截测试
- [ ] shell 高风险命令拦截测试
- [ ] `uv run` / `npx` 特定组合放行测试
- [ ] shell 默认超时与最大 timeout 测试
- [ ] 输出截断测试
- [ ] 参数校验与错误返回测试

## 实现收口

- [ ] 默认内置工具层已落地
- [ ] 权限边界已落地
- [ ] `exec` allowlist 与 deny guard 已落地
- [ ] `acceptance.md` 已与实现同步

## 依赖

- 依赖 `010-agent-runtime-foundation` 已完成

## 备注

- 当前不做浏览器内置工具；浏览器能力由 skill 通过脚本和 `exec` 实现。
