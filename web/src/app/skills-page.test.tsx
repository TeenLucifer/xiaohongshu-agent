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

describe("skills page feature", () => {
  it("renders the skills page from the dedicated route", async () => {
    renderWithRoute("/skills");

    expect(await screen.findByRole("heading", { name: "Skills", level: 1 })).toBeInTheDocument();
    expect(screen.getByText("xhs-explore")).toBeInTheDocument();
    expect(screen.getByText("xhs-auth")).toBeInTheDocument();
  });

  it("opens a detail dialog with metadata and summary", async () => {
    const user = userEvent.setup();
    renderWithRoute("/skills");

    await user.click(await screen.findByRole("button", { name: /xhs-explore/ }));

    const dialog = await screen.findByRole("dialog");

    expect(within(dialog).getByText("搜索与查看小红书帖子。")).toBeInTheDocument();
    expect(within(dialog).getByText("/repo/skills/xiaohongshu-skills/skills/xhs-explore/SKILL.md")).toBeInTheDocument();
    expect(within(dialog).getByText("先读取 SKILL.md，再执行搜索与帖子查看流程。")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "关闭 Skills 详情" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("navigates to the skills page from the sidebar", async () => {
    const user = userEvent.setup();
    renderWithRoute("/topics/topic-spring-commute");

    await user.click(await screen.findByRole("link", { name: "Skills" }));

    expect(await screen.findByRole("heading", { name: "Skills", level: 1 })).toBeInTheDocument();
  });
});
