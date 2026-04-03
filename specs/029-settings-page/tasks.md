# 029 Settings Page Tasks

## 当前状态

- [x] 已完成设置页方案收口，当前进入首版实现阶段。

## 已确认里程碑

- [x] 固定设置页路径为 `/settings`
- [x] 固定第一版只管理三类配置：
  - 主 LLM
  - 图片识别
  - 图片生成
- [x] 固定页面结构为“短标题区 + 顶部 tabs + 单主面板”
- [x] 固定每张卡支持“保存 + 测试”
- [x] 固定主 LLM 保存后立即刷新 runtime/provider

## 当前待办

- [x] 新增 `029-settings-page` 的前后端 spec 文档与导航
- [x] 在侧边栏中接入真实 `/settings` 路由入口
- [x] 实现 `GET /api/settings`
- [x] 实现三类配置的 `PUT` 保存接口
- [x] 实现三类配置的 `POST /test` 测试接口
- [x] 实现根 `.env` 的安全局部更新
- [x] 实现两个 skill `config.json` 的结构化更新
- [x] 实现主 LLM 配置保存后的 runtime/provider 热刷新
- [x] 实现前端设置页短标题区、tabs 与单主面板
- [x] 接入前端 settings API、mock 与测试

## 备注

- 本 feature 首版不做通用系统设置，只做三类模型配置管理。
