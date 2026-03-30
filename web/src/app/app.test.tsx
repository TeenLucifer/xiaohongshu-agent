import { render, screen } from "@testing-library/react";
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
  await screen.findByRole("region", { name: "Agent 对话主栏" });
}

describe("topic workspace feature", () => {
  it("renders the topic list on the home route", async () => {
    renderWithRoute("/");

    await waitForTopicList();

    expect(screen.getByRole("heading", { name: "新话题", level: 1 })).toBeInTheDocument();
    expect(screen.getAllByText("春季通勤穿搭").length).toBeGreaterThan(0);
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

  it("collapses and expands the right workspace panel", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");
    await waitForWorkspace();
    const shell = screen.getByTestId("workspace-shell");
    const contextColumn = screen.getByTestId("workspace-context-column");

    await user.click(screen.getByRole("button", { name: "收起工作区" }));

    expect(shell).toHaveAttribute("data-state", "collapsed");
    expect(shell).toHaveAttribute("data-grid-columns", "248px minmax(520px, 1fr) 72px");
    expect(contextColumn).toHaveAttribute("data-state", "collapsed");
    expect(contextColumn).toHaveAttribute("data-collapse-direction", "right");
    expect(screen.queryByText("内容面板")).not.toBeInTheDocument();
    expect(screen.queryByText("Context Panels")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "搜索结果", level: 2 })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开工作区" }));

    expect(shell).toHaveAttribute("data-state", "open");
    expect(shell).toHaveAttribute("data-grid-columns", "248px minmax(520px, 560px) minmax(560px, 1fr)");
    expect(contextColumn).toHaveAttribute("data-state", "open");
    expect(screen.getByText("内容面板")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "搜索结果", level: 2 })).toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: "设置" })).toBeInTheDocument();

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

  it("keeps the right panel collapsed when the left sidebar collapses afterward", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");
    await waitForWorkspace();
    const shell = screen.getByTestId("workspace-shell");

    await user.click(screen.getByRole("button", { name: "收起工作区" }));
    await user.click(screen.getByRole("button", { name: "收起侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "collapsed");
    expect(shell).toHaveAttribute("data-right-context", "collapsed");
    expect(shell).toHaveAttribute("data-grid-columns", "80px minmax(520px, 1fr) 72px");
    expect(screen.getByRole("button", { name: "展开工作区" })).toBeInTheDocument();
  });

  it("uses a compact chat composer instead of a large input card", async () => {
    renderWithRoute("/topics/topic-spring-commute");

    await waitForWorkspace();

    expect(screen.getByLabelText("对话输入框")).toHaveAttribute("type", "text");
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
});
