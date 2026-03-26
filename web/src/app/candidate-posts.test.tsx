import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

describe("candidate posts feature", () => {
  it("renders tiny image-first cards and uses the real reference image on the first card", () => {
    renderWorkspace();

    const cards = screen.getByRole("complementary", { name: "当前工作区" }).querySelectorAll("button[aria-haspopup='dialog']");
    expect(cards.length).toBeGreaterThanOrEqual(4);

    const firstImage = screen.getByRole("img", { name: "春日通勤西装 3 套搭法 封面图" }) as HTMLImageElement;
    expect(firstImage.src).toContain("ScreenShot_2026-03-26_201829_887.png");
    expect(screen.queryByRole("list", { name: "已选帖子顺序" })).not.toBeInTheDocument();
  });

  it("opens and closes the post detail modal via close button and escape", async () => {
    const user = userEvent.setup();
    renderWorkspace();

    await user.click(screen.getByRole("button", { name: /早八不费力通勤妆 \+ 穿搭/ }));

    const dialog = screen.getByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" });
    expect(within(dialog).getByText(/作者：晨间造型室/)).toBeInTheDocument();

    await user.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" })).not.toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /早八不费力通勤妆 \+ 穿搭/ }));
    await user.click(screen.getByRole("button", { name: "关闭" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" })).not.toBeInTheDocument();
    });
  });

  it("closes the modal when clicking the backdrop and toggles selection inside the modal", async () => {
    const user = userEvent.setup();
    const { container } = renderWorkspace();

    await user.click(screen.getByRole("button", { name: /早八不费力通勤妆 \+ 穿搭/ }));
    const dialog = screen.getByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" });

    await user.click(within(dialog).getByRole("button", { name: "加入已选" }));
    expect(within(dialog).getByRole("button", { name: "移出已选" })).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();

    const backdrop = container.querySelector("[role='presentation']");
    if (!(backdrop instanceof HTMLElement)) {
      throw new Error("backdrop not found");
    }
    fireEvent.click(backdrop);

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" })).not.toBeInTheDocument();
    });
  });

  it("supports manual ordering inside the modal and keeps order markers inline", async () => {
    const user = userEvent.setup();
    renderWorkspace();

    await user.click(screen.getByRole("button", { name: /低预算通勤衣橱整理术/ }));
    const dialog = screen.getByRole("dialog", { name: "低预算通勤衣橱整理术" });

    await user.click(within(dialog).getByRole("button", { name: "上移" }));

    await waitFor(() => {
      const firstSelectedCard = screen.getByRole("button", { name: /低预算通勤衣橱整理术/ });
      expect(firstSelectedCard).toBeInTheDocument();
      expect(screen.queryByRole("list", { name: "已选帖子顺序" })).not.toBeInTheDocument();
    });
  });
});
