# 014 Agent Tools Core Acceptance

## 手工验收

1. 初始化工具注册表
2. 注册全部文件系统工具和 `exec`
3. 在允许目录内执行 `read/write/edit/list`
4. 确认工具行为正常
5. 使用 `read_file` 读取一个图片文件
6. 确认图片读取行为符合 nanobot 风格
7. 使用 `edit_file` 进行一次模糊匹配替换
8. 确认替换成功
9. 尝试访问允许目录之外的路径
10. 确认文件系统工具返回越界错误
11. 使用 `exec` 执行一个 allowlist 内命令
12. 确认命令正常返回
13. 使用 `exec` 执行一个非 allowlist 命令
14. 确认命令被拒绝
15. 使用 `exec` 执行一个高风险命令
16. 确认命令被 deny guard 拦截
17. 使用 `uv run python ...` 或 `npx playwright ...` 验证特定包装组合可通过
18. 使用一个超时命令验证 `60s` 默认 timeout 行为
19. 使用大输出命令验证 head+tail 截断行为

## 自动化验收

- `ToolRegistry` 测试通过
- 文件系统工具测试通过
- `read_file` 图片读取测试通过
- `edit_file` 模糊匹配替换测试通过
- 文件系统越界测试通过
- shell 非 allowlist 命令拦截测试通过
- shell 风险拦截测试通过
- `uv run` / `npx` 特定组合测试通过
- shell 超时与最大 timeout 测试通过
- shell 输出截断测试通过
- 参数校验测试通过

## 已知限制

- 当前不包含浏览器工具
- 当前不包含 web search / web fetch
- 当前 `exec` 默认只放行固定命令前缀集合
