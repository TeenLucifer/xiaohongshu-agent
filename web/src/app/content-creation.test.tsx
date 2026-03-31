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
  await screen.findByRole("complementary", { name: "右侧面板" });
  return view;
}

describe("content creation feature", () => {
  it("renders summary in the main chat column and keeps structured content in the right workspace", async () => {
    await renderWorkspace();

    expect((await screen.findAllByText("标题会先切通勤场景")).length).toBeGreaterThan(0);
    expect(screen.queryByText("已生成一版完整文案，你可以直接在这里修改。")).not.toBeInTheDocument();
    expect(screen.queryByText("标题模式")).not.toBeInTheDocument();
  });

  it("shows the current copy draft in the right workspace panel", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    // 切换到"创作" tab
    await user.click(screen.getByRole("button", { name: "创作" }));

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
    expect(within(copyGroup).getByRole("button", { name: "重新生成文案" })).toBeInTheDocument();
  });

  it("shows copy summary and grouped images in the right workspace", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    // 总结在"选题" tab（默认显示）
    const summaryToggle = screen.getByRole("button", { name: "展开总结" });
    const summaryGroup = summaryToggle.closest("section");
    if (!(summaryGroup instanceof HTMLElement)) {
      throw new Error("summary group not found");
    }
    await user.click(summaryToggle);
    expect(within(summaryGroup).getByText("标题模式")).toBeInTheDocument();
    expect(within(summaryGroup).getByText("高频关键词")).toBeInTheDocument();
    expect(within(summaryGroup).getByRole("button", { name: "重新生成总结" })).toBeInTheDocument();

    // 切换到"创作" tab 查看文案和图片
    await user.click(screen.getByRole("button", { name: "创作" }));

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);
    expect(within(copyGroup).getByText("当前文案")).toBeInTheDocument();
    expect(within(copyGroup).getByRole("heading", { name: "通勤穿搭别再乱买了，4 件基础单品就够用", level: 3 })).toBeInTheDocument();

    const imageToggle = screen.getByRole("button", { name: "展开图片" });
    const imageGroup = imageToggle.closest("section");
    if (!(imageGroup instanceof HTMLElement)) {
      throw new Error("image group not found");
    }
    await user.click(imageToggle);
    expect(within(imageGroup).getByText(/^素材图片 \(\d+\)$/)).toBeInTheDocument();
    expect(within(imageGroup).getByText(/^编辑区 \(\d+\)$/)).toBeInTheDocument();
  });

  it("triggers summary and copy runs from the right panel buttons", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={["/topics/topic-small-rental"]}
      >
        <AppRoutes />
      </MemoryRouter>
    );

    await screen.findByRole("complementary", { name: "右侧面板" });

    // 总结在"选题" tab（默认显示）
    const summaryToggle = screen.getByRole("button", { name: "展开总结" });
    const summaryGroup = summaryToggle.closest("section");
    if (!(summaryGroup instanceof HTMLElement)) {
      throw new Error("summary group not found");
    }
    await user.click(summaryToggle);
    await user.click(within(summaryGroup).getByRole("button", { name: "生成总结" }));
    expect(
      await screen.findByText("请基于当前已选帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。")
    ).toBeInTheDocument();

    // 切换到"创作" tab 查看文案
    await user.click(screen.getByRole("button", { name: "创作" }));

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);
    await user.click(within(copyGroup).getByRole("button", { name: "生成文案" }));
    expect(
      await screen.findByText("请基于当前已选帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。")
    ).toBeInTheDocument();
  });
});
