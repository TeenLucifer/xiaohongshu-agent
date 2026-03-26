import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
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

describe("conversation timeline feature", () => {
  it("renders a simplified chat flow with only user and agent messages", () => {
    renderWorkspace();

    expect(screen.getByRole("list", { name: "对话消息流" })).toBeInTheDocument();
    expect(screen.getByText(/先围绕春季通勤穿搭去找一批高热度帖子/)).toBeInTheDocument();
    expect(screen.getByText(/第一轮搜集已经完成/)).toBeInTheDocument();
    expect(screen.queryByText("查看详细日志")).not.toBeInTheDocument();
    expect(screen.queryByText("输入摘要")).not.toBeInTheDocument();
  });

  it("keeps message layout lightweight and allows sending a new message", async () => {
    const user = userEvent.setup();
    renderWorkspace();

    await user.type(screen.getByLabelText("对话输入框"), "继续给我两版标题");
    await user.click(screen.getByRole("button", { name: "发送消息" }));

    expect(screen.getByText("继续给我两版标题")).toBeInTheDocument();
    expect(screen.getByText(/当前前端原型会先把结果保留在聊天主栏里/)).toBeInTheDocument();
  });
});
