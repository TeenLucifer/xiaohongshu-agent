import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
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
  await screen.findByRole("region", { name: "Agent 对话主栏" });
  return view;
}

describe("conversation timeline feature", () => {
  it("renders a simplified chat flow with only user and agent messages", async () => {
    await renderWorkspace();

    expect(screen.getByRole("list", { name: "对话消息流" })).toBeInTheDocument();
    expect(await screen.findByText(/先围绕春季通勤穿搭去找一批高热度帖子/)).toBeInTheDocument();
    expect(await screen.findByText(/第一轮搜集已经完成/)).toBeInTheDocument();
    expect(screen.queryByText("查看详细日志")).not.toBeInTheDocument();
    expect(screen.queryByText("输入摘要")).not.toBeInTheDocument();
  });

  it("keeps message layout lightweight and allows sending a new message", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    await renderWorkspace();

    await user.type(screen.getByLabelText("对话输入框"), "继续给我两版标题");
    await user.click(screen.getByRole("button", { name: "发送消息" }));

    expect(await screen.findByText("继续给我两版标题")).toBeInTheDocument();
    expect(await screen.findByText(/后端 API mock 已收到：继续给我两版标题/)).toBeInTheDocument();
    expect(
      fetchSpy.mock.calls.some((call) => {
        const input = call[0];
        const url =
          typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        return url.includes("/api/topics/topic-spring-commute/context");
      })
    ).toBe(true);
    fetchSpy.mockRestore();
  });
});
