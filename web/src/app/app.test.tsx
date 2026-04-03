import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./routes";

function renderWithRoute(initialEntry: string): ReturnType<typeof render> {
  return render(
    <MemoryRouter
      future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
      initialEntries={[initialEntry]}
    >
      <AppRoutes />
    </MemoryRouter>
  );
}

async function waitForTopicList(): Promise<void> {
  await screen.findByRole("heading", { name: "新话题", level: 1 });
  const matches = await screen.findAllByText("春季通勤穿搭");
  expect(matches.length).toBeGreaterThan(0);
}

async function waitForWorkspace(): Promise<void> {
  await screen.findByTestId("workspace-shell");
  await screen.findByTestId("workspace-main-panel");
}

describe("topic workspace feature", () => {
  it("renders the topic list on the home route", async () => {
    renderWithRoute("/");

    await waitForTopicList();

    expect(screen.getByRole("heading", { name: "新话题", level: 1 })).toBeInTheDocument();
    expect(screen.getByLabelText("话题标题").tagName).toBe("INPUT");
    expect(screen.getAllByText("春季通勤穿搭").length).toBeGreaterThan(0);
    expect(screen.getByTestId("recent-topics-rail")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-sidebar")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "新话题" })).toBeInTheDocument();
  });

  it("creates a topic and navigates to its workspace", async () => {
    const user = userEvent.setup();
    renderWithRoute("/");

    await waitForTopicList();

    await user.type(screen.getByLabelText("话题标题"), "新的测试话题");
    await user.click(screen.getByRole("button", { name: "创建话题" }));

    expect(
      await screen.findByRole("heading", { name: "新的测试话题", level: 1 })
    ).toBeInTheDocument();
  });

  it("switches topic from the sidebar", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    await user.click(screen.getByRole("link", { name: /租房小户型改造/ }));

    expect(
      await screen.findByRole("heading", { name: "租房小户型改造", level: 1 })
    ).toBeInTheDocument();
  });

  it("renders a workspace-first layout with creation and conversation tabs", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");
    await waitForWorkspace();
    const shell = screen.getByTestId("workspace-shell");

    expect(shell).toHaveAttribute("data-layout", "workspace-tabs");
    expect(screen.queryByText("Topic Workspace")).not.toBeInTheDocument();
    expect(screen.queryByText("已就绪")).not.toBeInTheDocument();
    expect(screen.queryByText("进行中")).not.toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "创作" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: "选题" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "对话" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "展开素材" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("对话输入框")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "对话" }));

    expect(await screen.findByLabelText("对话输入框")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-conversation-tab")).toBeInTheDocument();
    expect(screen.queryByText("Conversation")).not.toBeInTheDocument();
    expect(screen.queryByText("对话记录")).not.toBeInTheDocument();
  });

  it("collapses and expands the left sidebar while keeping the main workspace available", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");
    await waitForWorkspace();
    const shell = screen.getByTestId("workspace-shell");
    const sidebar = screen.getByTestId("workspace-sidebar");

    await user.click(screen.getByRole("button", { name: "收起侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "collapsed");
    expect(sidebar).toHaveAttribute("data-state", "collapsed");
    expect(screen.queryByRole("link", { name: /春季通勤穿搭/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "展开侧边栏" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "新话题" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Skills" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "设置" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "open");
    expect(sidebar).toHaveAttribute("data-state", "open");
    expect(screen.getByRole("link", { name: "新话题" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "当前会话" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "历史记录" })).not.toBeInTheDocument();
  });

  it("renders the sidebar flush to the viewport edge without rounded corners", async () => {
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    const sidebar = screen.getByTestId("workspace-sidebar");

    expect(sidebar.className).toContain("h-screen");
    expect(sidebar.className).toContain("border-r");
    expect(sidebar.className).not.toContain("rounded");
  });

  it("keeps the main workspace full-width when the left sidebar collapses", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");
    await waitForWorkspace();
    const shell = screen.getByTestId("workspace-shell");

    await user.click(screen.getByRole("button", { name: "收起侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "collapsed");
    expect(shell).toHaveAttribute("data-grid-columns", "80px minmax(0, 1fr)");
  });

  it("shows the compact composer only inside the conversation tab", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    expect(screen.queryByLabelText("对话输入框")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "对话" }));
    expect(screen.getByLabelText("对话输入框").tagName).toBe("TEXTAREA");
    expect(screen.getByRole("button", { name: "发送消息" })).toBeInTheDocument();
    expect(screen.queryByText("查看详细日志")).not.toBeInTheDocument();
  });

  it("deletes the current topic and navigates to the next remaining topic", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    await user.click(screen.getByRole("button", { name: "删除当前话题" }));

    expect(
      await screen.findByRole("heading", { name: "租房小户型改造", level: 1 })
    ).toBeInTheDocument();
  });

  it("navigates back to the home entry from the sidebar new topic link", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    await user.click(screen.getByRole("link", { name: "新话题" }));

    expect(await screen.findByRole("heading", { name: "新话题", level: 1 })).toBeInTheDocument();
  });

  it("opens the settings page from the sidebar", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    await user.click(screen.getByRole("link", { name: "设置" }));

    expect(await screen.findByTestId("settings-shell")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "设置", level: 1 })).toBeInTheDocument();
    expect(screen.getByTestId("settings-tabs")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "主 LLM" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "图片识别" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "图片生成" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("heading", { name: "主 LLM", level: 2 })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "图片识别", level: 2 })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "图片生成", level: 2 })).not.toBeInTheDocument();
  });

  it("saves and tests provider settings on the settings page", async () => {
    const user = userEvent.setup();
    renderWithRoute("/settings");

    expect(await screen.findByTestId("settings-shell")).toBeInTheDocument();
    const llmCard = screen.getByTestId("settings-card-主 LLM");
    const baseUrlInput = within(llmCard).getByDisplayValue("https://api.openai.com/v1");

    await user.clear(baseUrlInput);
    await user.type(baseUrlInput, "https://llm.changed.test/v1");
    await user.click(within(llmCard).getByRole("button", { name: "保存" }));

    expect(await within(llmCard).findByText("保存成功，后续调用将使用新配置。")).toBeInTheDocument();

    await user.click(within(llmCard).getByRole("button", { name: "测试" }));

    expect(await within(llmCard).findByText("主 LLM 连接成功。")).toBeInTheDocument();
  });

  it("switches between settings tabs and shows a single active panel", async () => {
    const user = userEvent.setup();
    renderWithRoute("/settings");

    expect(await screen.findByTestId("settings-shell")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "主 LLM", level: 2 })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "图片生成" }));

    expect(screen.getByRole("button", { name: "图片生成" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("heading", { name: "主 LLM", level: 2 })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "图片生成", level: 2 })).toBeInTheDocument();
    expect(screen.queryByTestId("settings-card-主 LLM")).not.toBeInTheDocument();
    expect(screen.getByTestId("settings-card-图片生成")).toBeInTheDocument();
  });

  it("reveals the configured api key after clicking the visibility toggle", async () => {
    const user = userEvent.setup();
    renderWithRoute("/settings");

    expect(await screen.findByTestId("settings-shell")).toBeInTheDocument();

    const llmCard = screen.getByTestId("settings-card-主 LLM");
    const apiKeyInput = within(llmCard).getByLabelText("API Key", { selector: "input" });

    expect(apiKeyInput).toHaveAttribute("type", "text");
    expect(apiKeyInput).toHaveValue("***************");

    await user.click(within(llmCard).getByRole("button", { name: "显示 API Key" }));

    expect(apiKeyInput).toHaveAttribute("type", "text");
    expect(apiKeyInput).toHaveValue("sk-llm-test-key");
  });
});
