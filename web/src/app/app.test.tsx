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

describe("topic workspace feature", () => {
  it("renders the workspace directly on the home route", () => {
    renderWithRoute("/");

    expect(screen.getByRole("heading", { name: "春季通勤穿搭", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "主导航" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Agent 对话主栏" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "当前工作区" })).toBeInTheDocument();
  });

  it("switches topic from the sidebar", async () => {
    const user = userEvent.setup();
    renderWithRoute("/");

    await user.click(screen.getByRole("link", { name: /租房小户型改造/ }));

    expect(screen.getByRole("heading", { name: "租房小户型改造", level: 1 })).toBeInTheDocument();
  });

  it("collapses and expands the right workspace panel", async () => {
    const user = userEvent.setup();
    renderWithRoute("/");
    const shell = screen.getByTestId("workspace-shell");
    const contextColumn = screen.getByTestId("workspace-context-column");

    await user.click(screen.getByRole("button", { name: "收起工作区" }));

    expect(shell).toHaveAttribute("data-state", "collapsed");
    expect(contextColumn).toHaveAttribute("data-state", "collapsed");
    expect(screen.queryByRole("heading", { name: "搜索结果", level: 2 })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开工作区" }));

    expect(shell).toHaveAttribute("data-state", "open");
    expect(contextColumn).toHaveAttribute("data-state", "open");
    expect(screen.getByRole("heading", { name: "搜索结果", level: 2 })).toBeInTheDocument();
  });

  it("collapses and expands the left sidebar while keeping the main workspace available", async () => {
    const user = userEvent.setup();
    renderWithRoute("/");
    const shell = screen.getByTestId("workspace-shell");
    const sidebar = screen.getByTestId("workspace-sidebar");

    await user.click(screen.getByRole("button", { name: "收起侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "collapsed");
    expect(sidebar).toHaveAttribute("data-state", "collapsed");
    expect(screen.queryByRole("link", { name: /春季通勤穿搭/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "展开侧边栏" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "当前会话" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "历史记录" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Skills" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "设置" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "open");
    expect(sidebar).toHaveAttribute("data-state", "open");
    expect(screen.getByRole("button", { name: "当前会话" })).toBeInTheDocument();
  });

  it("renders the sidebar flush to the viewport edge without rounded corners", () => {
    renderWithRoute("/");

    const sidebar = screen.getByTestId("workspace-sidebar");

    expect(sidebar.className).toContain("h-screen");
    expect(sidebar.className).toContain("border-r");
    expect(sidebar.className).not.toContain("rounded");
  });

  it("keeps the right panel collapsed when the left sidebar collapses afterward", async () => {
    const user = userEvent.setup();
    renderWithRoute("/");
    const shell = screen.getByTestId("workspace-shell");

    await user.click(screen.getByRole("button", { name: "收起工作区" }));
    await user.click(screen.getByRole("button", { name: "收起侧边栏" }));

    expect(shell).toHaveAttribute("data-left-sidebar", "collapsed");
    expect(shell).toHaveAttribute("data-right-context", "collapsed");
    expect(screen.getByRole("button", { name: "展开工作区" })).toBeInTheDocument();
  });

  it("uses a compact chat composer instead of a large input card", () => {
    renderWithRoute("/");

    expect(screen.getByLabelText("对话输入框")).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: "发送消息" })).toBeInTheDocument();
    expect(screen.queryByText("查看详细日志")).not.toBeInTheDocument();
  });
});
