<div align="center">

# 小红书运营 Agent 工作台

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vite.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Lexical](https://img.shields.io/badge/Lexical-Editor-black?style=flat-square)](https://lexical.dev/)

围绕一个具体话题，把搜帖、总结、文案、图片创作和对话执行记录收进同一个工作区。

[**核心功能**](#-核心功能介绍) · [**功能展示**](#-动图展示核心功能) · [**框架介绍**](#-框架介绍) · [**部署方式**](#-部署方式) · [**核心模块**](#-核心模块详细介绍)

</div>

<div align="center">

🔎 **小红书帖子自动化搜集** &nbsp;•&nbsp; 🧠 **人在回路的文案与图片创作**<br>

</div>

---

## ✨ 核心功能介绍

### 🔎 小红书帖子自动化搜集
围绕一个话题执行发散式搜集，拉取帖子详情并下载标准帖子包。搜索结果直接进入工作区，用户可以删掉无用帖子，剩余结果天然进入后续创作链路。

### 🧠 人在回路的文案与图片创作
基于当前保留帖子生成总结，再进入文案白板继续改写，并在图片区上传参考图、整理编辑区和生成图片。整个过程保留人工判断，Agent 负责执行重复性分析、改写和生成动作。

---

## 🎬 动图展示核心功能

当前 README 先保留展示位，后续补真实 GIF 或截图。

<table>
<tr>
<td width="100%" align="center" valign="top">

<h3>🔎 小红书帖子自动化搜集</h3>
<img src="assets/readme/search-and-summary.gif" alt="搜索结果与总结" width="100%">
<br>
<sub>发散搜集帖子、获取详情、落盘帖子包，并在工作区中删除无用结果</sub>

</td>
</tr>
</table>

<table>
<tr>
<td width="33%" align="center" valign="top">

<h3>🧠 文案白板与 AI 润色</h3>
<img src="assets/readme/copy-editor.gif" alt="文案白板与 AI 润色" width="100%">
<br>
<sub>Markdown 白板编辑、选区润色、自动保存</sub>

</td>
<td width="33%" align="center" valign="top">

<h3>🖼️ 图片上传与生成</h3>
<img src="assets/readme/image-generation.gif" alt="图片上传与生成" width="100%">
<br>
<sub>上传参考图、拖入编辑区、生成图片结果</sub>

</td>
<td width="33%" align="center" valign="top">

<h3>💬 对话记录与执行反馈</h3>
<img src="assets/readme/conversation.gif" alt="对话记录与执行反馈" width="100%">
<br>
<sub>统一查看 user / agent 对话、tool 摘要和流式结果</sub>

</td>
</tr>
</table>

---

## 🏛️ 框架介绍

<div align="center">
<img src="assets/readme/framework.png" alt="小红书运营 Agent 工作台框架图" width="100%">
</div>

### 🖥️ 工作区层
产品以“话题”为工作单元。当前界面收口为 `创作 / 对话` 两个 tab，其中 `创作` 负责把“帖子自动化搜集”与“人在回路创作”串在一起，`对话` 统一承接交互结果与执行反馈。

### 🤖 Agent 与 Skills 层
系统采用“一个主 Agent + 多个业务 Skills”的组织方式。一组技能负责小红书帖子搜集、详情获取和帖子包落盘，另一组技能负责总结、文案改写、图片分析、图片生成与选区润色。

### 💾 后端与数据层
后端负责 topic/session 映射、run 调用、流式输出和 workspace 文件化存储。帖子包、总结、文案和图片结果都统一落在当前 session workspace 中，前端再从同一个 context 中读取和展示。

---

## 🚀 部署方式

### 前端

```bash
cd web
npm install
npm run dev
```

### 后端

```bash
PYTHONPATH=src .venv/bin/python -m backend.app
```

如果希望前端显式指向本地后端：

```bash
cd web
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

### 本地 Agent 联调

```bash
PYTHONPATH=src .venv/bin/python -m agent.local_harness run \
  --topic "联调测试" \
  --user-input "smoke run" \
  --trace
```

### 常用命令

```bash
cd web
npm test
npm run test:e2e
npm run build
```

```bash
PYTHONPATH=src .venv/bin/pytest -q
```

---

## 📦 核心模块详细介绍

### 小红书帖子自动化搜集
这一部分负责把研究输入准备好。Agent 会围绕话题做发散式搜集、获取详情、下载图文帖子包，搜索结果直接进入工作区顶部。用户只需要删除明显无用的帖子，剩余结果就会成为后续创作输入。

#### 搜索结果工作区
搜索结果位于 `创作` 顶部，支持查看详情、预览图片、继续发消息让 Agent 深挖，或直接删除无用帖子。这里不再区分“已选帖子”，留下来的结果默认就是可用结果。

#### 总结沉淀
总结作为搜索结果下方的一部分展示，直接基于当前剩余帖子生成。它不是独立页面，而是搜集结果的自然下游，用来帮助用户快速进入创作阶段。

### 人在回路的文案与图片创作
这一部分负责把研究结果变成可发布内容。核心原则是“人工决策在前，Agent 负责提效”，所以文案和图片都在工作区里持续编辑，而不是一次性生成后结束。

#### 文案白板
文案区是单层 Markdown 白板，不是传统表单。它支持连续编辑、自动保存、快捷语法渲染和选区 AI 润色，更接近真实创作场景中的持续修改体验。

#### 图片创作
图片区承接本地图片上传、候选图预览、编辑区拖拽和图片生成结果。参考图和生成结果都继续留在当前工作区内，方便反复调整和复用。

#### 对话记录
`对话` tab 是这一整条创作链路的统一执行记录区。无论消息从主输入框发起，还是从搜索结果区、图片区局部输入框发起，最终都会回到同一条消息流中，方便回看执行结果和 tool 摘要。

---

## 🔧 技术栈

- 前端：React + Vite + Tailwind CSS + Framer Motion
- 编辑器：Lexical + Markdown
- 后端：FastAPI
- Agent：Python 3.11+，基于 session / memory / loop / tools / skills 的本地 runtime
- 测试：Vitest + Playwright + pytest + pyright + ruff

## 📁 仓库结构

```text
specs/     功能规格、任务拆分与验收标准
web/       前端工作台
src/       Agent runtime、后端、memory、tools、skills loader 等代码
skills/    业务型 skills 与小红书技能集合
docs/      架构说明、术语表和技术决策
```

## 📚 开发与文档

- 协作规则和 specs 导航见 [AGENTS.md](./AGENTS.md)
- 架构说明见 [docs/architecture.md](./docs/architecture.md)
- 技术决策见 [docs/tech-decisions.md](./docs/tech-decisions.md)

如果 README、AGENTS 和 specs 有冲突，以 `specs/` 为准。
