# 术语表

- `Feature`
  - 一个独立推进的能力单元，对应 `specs/<feature>/`

- `spec.md`
  - 需求与边界文档，定义做什么和不做什么

- `tasks.md`
  - 实施顺序文档，定义开发子步骤、测试优先任务和实现任务

- `acceptance.md`
  - 验收文档，定义手工和自动化验收路径

- `质量门禁`
  - `ruff check`、`ruff format --check`、`pyright`、`pytest -q`

- `schema`
  - 跨层输入输出的结构化类型定义

- `service`
  - 负责完成一个业务用例的编排层

- `adapter`
  - 用于隔离外部系统、模型接口或持久化实现的边界层

- `starter repo`
  - 可以直接复制为新仓库起点的模板项目，不是代码生成器
