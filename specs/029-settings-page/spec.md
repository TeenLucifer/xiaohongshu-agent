# 029 Settings Page

## 背景

当前侧边栏已经有“设置”入口，但它仍然是占位按钮，没有真实页面、没有配置读写链路，也无法通过前端管理主 LLM、图片识别和图片生成所依赖的配置。

与此同时，当前仓库的模型配置已经真实分散在三处：

- 主 LLM：根目录 `.env`
- 图片识别：`skills/image-analysis/config.json`
- 图片生成：`skills/image-generation/config.json`

如果继续完全依赖手改文件，配置切换成本高，也不利于后续联调与演示。

## 目标

- 提供一个正式的 `/settings` 页面
- 让侧边栏“设置”成为真实导航入口
- 第一版只管理三类配置：
  - 主 LLM
  - 图片识别
  - 图片生成
- 页面结构采用：
  - 顶部标题区
  - 顶部 tabs
  - 单一主内容面板
- 不做 DeepTutor 那种完整多系统设置中心，但保留 tabs 结构
- 每个 tab 的主面板支持：
  - 查看当前 `base_url`、`model`
  - 查看 API Key 是否已配置
  - 修改并保存
  - 单独测试连接
- 主 LLM 配置保存后立即刷新 runtime/provider，使后续 run 直接生效
- 图片识别和图片生成继续沿用各自 skill 目录内的 `config.json`

## 非目标

- 不实现主题、语言、本地缓存等通用设置
- 不实现多 provider 切换列表、配置历史或配置版本管理
- 不重构当前 skill 配置文件路径
- 不改现有 run / stream / context / messages 协议

## 用户故事

- 作为使用者，我希望可以直接在产品里配置主 LLM，而不是手改 `.env`
- 作为使用者，我希望可以分别配置图片识别和图片生成所需的 API，而不是去 skill 目录找 `config.json`
- 作为使用者，我希望修改配置后能立即测试连通性，避免保存一组明显不可用的配置
- 作为使用者，我希望主 LLM 保存后后续对话直接走新配置，而不是还要手动重启服务

## 输入输出

- 输入：
  - 根 `.env`
  - `skills/image-analysis/config.json`
  - `skills/image-generation/config.json`
- 输出：
  - `/settings` 设置页
  - 三类配置的读取、写回与连接测试能力

## 约束

- 前端代码放在 `web/`
- 后端继续放在 `src/backend/`
- 主 LLM 配置继续以根 `.env` 为真实来源
- 图片识别与图片生成继续以各自 skill 目录下的 `config.json` 为真实来源
- 设置页第一版只展示和编辑：
  - `base_url`
  - `api_key`
  - `model`
- 图片生成的 `size` 继续保留在 `config.json`，但不进入第一版 UI
- API Key 默认以普通字符节奏的星号掩码回填当前值，并支持通过小眼睛切换显示真实值
- 保存与测试是两个独立动作
- `POST /test` 必须测试用户当前提交值，而不是只测试已保存配置
- 主 LLM 保存后必须刷新 runtime/provider，而不是要求重启服务

## 验收标准

- 侧边栏点击“设置”后可进入 `/settings`
- 设置页首屏呈现为：
  - 标题区
  - 顶部 tabs
  - 单一主内容面板
- tabs 包含：
  - 主 LLM
  - 图片识别
  - 图片生成
- 默认激活“主 LLM”
- 每次只显示一个激活 tab 对应的主面板
- 激活面板能展示当前 `base_url`、`model` 和 API Key 是否已配置
- API Key 默认以普通星号掩码显示，但点击可切换为真实值
- 用户可输入新 key 覆盖旧 key
- 每个 tab 面板都支持“保存”和“测试”
- 主 LLM 保存成功后，后续 run 直接使用新配置
- 图片识别和图片生成保存成功后，后续 skill 调用直接使用新配置
- 主 LLM、图片识别、图片生成都能返回明确的测试成功/失败反馈
- 设置页风格与当前工作区一致，不是单独的一套产品视觉
