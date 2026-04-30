import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { AppRoutes } from "./routes";

async function renderWorkspace(): Promise<ReturnType<typeof render>> {
  const user = userEvent.setup();
  const view = render(
    <MemoryRouter
      future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
      initialEntries={["/topics/topic-spring-commute"]}
    >
      <AppRoutes />
    </MemoryRouter>
  );
  await screen.findByTestId("workspace-main-panel");
  await user.click(await screen.findByRole("button", { name: "对话" }));
  await screen.findByTestId("workspace-conversation-tab");
  return view;
}

describe("conversation timeline feature", () => {
  it("renders a simplified chat flow with only user and agent messages", async () => {
    await renderWorkspace();

    expect(screen.getByRole("list", { name: "对话消息流" })).toBeInTheDocument();
    expect(screen.queryByText("Conversation")).not.toBeInTheDocument();
    expect(screen.queryByText("对话记录")).not.toBeInTheDocument();
    expect(screen.queryByText("这里集中展示 user / agent 对话结果与执行反馈。")).not.toBeInTheDocument();
    expect(await screen.findByText(/先围绕春季通勤穿搭去找一批高热度帖子/)).toBeInTheDocument();
    expect(await screen.findByText(/第一轮搜集已经完成/)).toBeInTheDocument();
    expect(screen.queryByText("查看详细日志")).not.toBeInTheDocument();
    expect(screen.queryByText("输入摘要")).not.toBeInTheDocument();
  });

  it("shows only the final answer while keeping tool calls in a collapsed summary", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    expect(screen.queryByText("准备调用工具")).not.toBeInTheDocument();
    const summaryToggle = await screen.findByText(/工具调用摘要/);
    expect(summaryToggle).toBeInTheDocument();

    await user.click(summaryToggle);

    expect(await screen.findByText("xhs-explore")).toBeInTheDocument();
    expect(screen.getByText(/参数：/)).toBeInTheDocument();
    expect(screen.getByText(/结果：/)).toBeInTheDocument();
  });

  it("renders agent messages with markdown while keeping user messages as plain text", async () => {
    await renderWorkspace();

    expect((await screen.findAllByText("标题会先切通勤场景")).length).toBeGreaterThan(0);
    expect(screen.getByText("正文更强调“直接照搬”的效率感。")).toBeInTheDocument();
    expect(screen.getByText("维度")).toBeInTheDocument();
    expect(screen.getByText("可优先保留", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("基于我已经选中的帖子，总结一下标题和正文结构，再给我一版完整文案。")).toBeInTheDocument();
  });

  it("keeps message layout lightweight and allows sending a new message", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const originalScrollTo = HTMLElement.prototype.scrollTo;
    const scrollToSpy = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: scrollToSpy,
    });
    await renderWorkspace();

    const composer = screen.getByLabelText("对话输入框");
    expect(composer.tagName).toBe("TEXTAREA");
    await user.type(composer, "继续给我两版标题");
    await user.click(screen.getByRole("button", { name: "发送消息" }));

    expect(await screen.findByText("继续给我两版标题")).toBeInTheDocument();
    expect(await screen.findByText(/后端 API mock 已收到：继续给我两版标题/)).toBeInTheDocument();
    expect(composer).toHaveValue("");
    expect(
      fetchSpy.mock.calls.some((call) => {
        const input = call[0];
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        return url.includes("/api/topics/topic-spring-commute/context");
      })
    ).toBe(true);
    expect(scrollToSpy).toHaveBeenCalled();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: originalScrollTo,
    });
    fetchSpy.mockRestore();
  });

  it("shows a jump-to-bottom button after the user scrolls up and avoids forced auto-scroll", async () => {
    const user = userEvent.setup();
    const originalScrollTo = HTMLElement.prototype.scrollTo;
    const scrollToSpy = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: scrollToSpy,
    });

    await renderWorkspace();

    const scrollContainer = screen.getByTestId("conversation-scroll-container");
    Object.defineProperty(scrollContainer, "scrollHeight", {
      configurable: true,
      value: 1200,
    });
    Object.defineProperty(scrollContainer, "clientHeight", {
      configurable: true,
      value: 400,
    });
    Object.defineProperty(scrollContainer, "scrollTop", {
      configurable: true,
      writable: true,
      value: 500,
    });

    fireEvent.scroll(scrollContainer);

    expect(await screen.findByRole("button", { name: "跳转到底部" })).toBeInTheDocument();

    scrollToSpy.mockClear();
    const composer = screen.getByLabelText("对话输入框");
    await user.type(composer, "继续补充一轮帖子");
    await user.click(screen.getByRole("button", { name: "发送消息" }));

    expect(await screen.findByText("继续补充一轮帖子")).toBeInTheDocument();
    expect(scrollToSpy).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "跳转到底部" }));

    expect(scrollToSpy).toHaveBeenCalled();
    expect(scrollToSpy).toHaveBeenLastCalledWith(
      expect.objectContaining({ behavior: "smooth" })
    );
    expect(screen.queryByRole("button", { name: "跳转到底部" })).not.toBeInTheDocument();

    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: originalScrollTo,
    });
  });
});
