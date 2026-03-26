import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { within } from "@testing-library/react";
import { AppRoutes } from "./routes";

function renderWorkspace(): ReturnType<typeof render> {
  return render(
    <MemoryRouter
      future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
      initialEntries={["/topics/topic-spring-commute"]}
    >
      <AppRoutes />
    </MemoryRouter>
  );
}

describe("content creation feature", () => {
  it("renders summary and copy as agent replies in the main chat column", () => {
    renderWorkspace();

    expect(screen.getByText(/这批内容的共性很稳定/)).toBeInTheDocument();
    expect(screen.getByText("已生成一版完整文案，你可以直接在这里修改。")).toBeInTheDocument();
    expect(screen.queryByText("标题模式")).not.toBeInTheDocument();
  });

  it("opens the copy reply into edit mode and edits the draft", async () => {
    const user = userEvent.setup();
    renderWorkspace();

    expect(screen.queryByLabelText("笔记标题")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "编辑" }));

    const titleInput = screen.getByLabelText("笔记标题");
    const bodyInput = screen.getByLabelText("笔记正文");

    expect(titleInput).toHaveValue("通勤穿搭别再乱买了，4 件基础单品就够用");

    await user.clear(titleInput);
    await user.type(titleInput, "新的通勤标题");
    await user.type(bodyInput, "\n补一段结尾。");

    expect(titleInput).toHaveValue("新的通勤标题");
    expect((bodyInput as HTMLTextAreaElement).value).toContain("补一段结尾。");
  });

  it("shows copy summary and grouped images in the right workspace", async () => {
    const user = userEvent.setup();
    renderWorkspace();

    await user.click(screen.getByRole("button", { name: "展开文案" }));
    const copyGroup = screen.getByRole("heading", { name: "文案", level: 2 }).closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    expect(within(copyGroup).getByText("当前文案")).toBeInTheDocument();
    expect(within(copyGroup).getByRole("heading", { name: "通勤穿搭别再乱买了，4 件基础单品就够用", level: 3 })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "展开图片" }));
    expect(screen.getByRole("heading", { name: "文生图", level: 3 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "图生图", level: 3 })).toBeInTheDocument();
    expect(screen.getAllByAltText(/候选图/).length).toBeGreaterThan(0);
  });
});
