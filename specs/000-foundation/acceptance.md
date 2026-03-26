# 000 Foundation Acceptance

## 手工验收

1. 执行 `uv sync`
2. 执行 `uv run pytest -q`
3. 确认基础测试通过

## 自动化验收

- 配置模型测试通过
- 日志与异常测试通过

## 已知限制
- 本模板只提供最小工程骨架，不替代业务级架构设计。

## 演示路径
1. 执行 `uv sync`
2. 执行 `uv run pytest -q`
3. 执行 `uv run pyright`
4. 确认基础工程链路可运行
