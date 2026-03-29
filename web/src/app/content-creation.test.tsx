import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./routes";

async function renderWorkspace(): Promise<ReturnType<typeof render>> {
  const view = render(
    <MemoryRouter
      future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
      initialEntries={["/topics/topic-spring-commute"]}
    >
      <AppRoutes />
    </MemoryRouter>
  );
  await screen.findByRole("complementary", { name: "当前工作区" });
  return view;
}

describe("content creation feature", () => {
  it("renders summary in the main chat column and keeps structured content in the right workspace", async () => {
    await renderWorkspace();

    expect(await screen.findByText(/这批内容的共性很稳定/)).toBeInTheDocument();
    expect(screen.queryByText("已生成一版完整文案，你可以直接在这里修改。")).not.toBeInTheDocument();
    expect(screen.queryByText("标题模式")).not.toBeInTheDocument();
  });

  it("shows the current copy draft in the right workspace panel", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }

    await user.click(copyToggle);

    expect(within(copyGroup).getByText("当前文案")).toBeInTheDocument();
    expect(
      within(copyGroup).getByRole("heading", {
        name: "通勤穿搭别再乱买了，4 件基础单品就够用",
        level: 3
      })
    ).toBeInTheDocument();
    expect(within(copyGroup).queryByRole("button", { name: "编辑" })).not.toBeInTheDocument();
  });

  it("shows copy summary and grouped images in the right workspace", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    const summaryToggle = screen.getByRole("button", { name: "展开总结" });
    const summaryGroup = summaryToggle.closest("section");
    if (!(summaryGroup instanceof HTMLElement)) {
      throw new Error("summary group not found");
    }
    await user.click(summaryToggle);
    expect(within(summaryGroup).getByText("标题模式")).toBeInTheDocument();
    expect(within(summaryGroup).getByText("高频关键词")).toBeInTheDocument();

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);
    expect(within(copyGroup).getByText("当前文案")).toBeInTheDocument();
    expect(within(copyGroup).getByRole("heading", { name: "通勤穿搭别再乱买了，4 件基础单品就够用", level: 3 })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开图片" }));
    expect(screen.getByRole("heading", { name: "文生图", level: 3 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "图生图", level: 3 })).toBeInTheDocument();
    expect(screen.getAllByAltText(/候选图/).length).toBeGreaterThan(0);
  });
});
