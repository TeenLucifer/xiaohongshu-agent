import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  await screen.findByRole("button", { name: /春日通勤西装 3 套搭法/ });
  return view;
}

describe("candidate posts feature", () => {
  it("renders tiny image-first cards and uses the real reference image on the first card", async () => {
    await renderWorkspace();

    const cards = screen.getByRole("complementary", { name: "右侧面板" }).querySelectorAll("button[aria-haspopup='dialog']");
    expect(cards.length).toBeGreaterThanOrEqual(4);

    const firstImage = screen.getByRole("img", { name: "春日通勤西装 3 套搭法 封面图" }) as HTMLImageElement;
    expect(firstImage.src).toContain("ScreenShot_2026-03-26_201829_887.png");
    expect(screen.queryByRole("list", { name: "已选帖子顺序" })).not.toBeInTheDocument();
  });

  it("opens and closes the post detail modal via close button and escape", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

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
    const { container } = await renderWorkspace();

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
    await renderWorkspace();

    await user.click(screen.getByRole("button", { name: /低预算通勤衣橱整理术/ }));
    const dialog = screen.getByRole("dialog", { name: "低预算通勤衣橱整理术" });

    await user.click(within(dialog).getByRole("button", { name: "上移" }));

    await waitFor(() => {
      const firstSelectedCard = screen.getByRole("button", { name: /低预算通勤衣橱整理术/ });
      expect(firstSelectedCard).toBeInTheDocument();
      expect(screen.queryByRole("list", { name: "已选帖子顺序" })).not.toBeInTheDocument();
    });
  });

  it("supports multi-image paging inside the post detail modal", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    await user.click(screen.getByRole("button", { name: /春日通勤西装 3 套搭法/ }));
    const dialog = screen.getByRole("dialog", { name: "春日通勤西装 3 套搭法" });

    expect(within(dialog).getByRole("img", { name: "候选帖图片 1" })).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "上一张图片" })).toBeDisabled();
    expect(within(dialog).getByRole("button", { name: "下一张图片" })).toBeEnabled();

    await user.click(within(dialog).getByRole("button", { name: "下一张图片" }));
    expect(within(dialog).getByRole("img", { name: "候选帖图片 2" })).toBeInTheDocument();

    await user.keyboard("{ArrowRight}");
    expect(within(dialog).getByRole("img", { name: "候选帖图片 3" })).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "下一张图片" })).toBeDisabled();

    await user.keyboard("{ArrowLeft}");
    expect(within(dialog).getByRole("img", { name: "候选帖图片 2" })).toBeInTheDocument();
  });

  it("opens a lightbox when clicking the detail image and supports preview navigation", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    await user.click(screen.getByRole("button", { name: /春日通勤西装 3 套搭法/ }));
    const detailDialog = screen.getByRole("dialog", { name: "春日通勤西装 3 套搭法" });

    await user.click(within(detailDialog).getByRole("img", { name: "候选帖图片 1" }));
    const lightbox = screen.getByRole("dialog", { name: "图片预览" });
    expect(within(lightbox).getByRole("img", { name: "候选帖图片 1" })).toBeInTheDocument();

    await user.click(within(lightbox).getByRole("button", { name: "下一张预览图片" }));
    expect(within(lightbox).getByRole("img", { name: "候选帖图片 2" })).toBeInTheDocument();

    await user.keyboard("{Escape}");
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "图片预览" })).not.toBeInTheDocument();
    });
  });

  it("keeps single-image posts on the current detail layout without paging controls", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    await user.click(screen.getByRole("button", { name: /薄针织 \+ 西裤，通勤一周不重样/ }));
    const dialog = screen.getByRole("dialog", { name: "薄针织 + 西裤，通勤一周不重样" });

    expect(within(dialog).getByRole("img", { name: "候选帖图片 1" })).toBeInTheDocument();
    expect(within(dialog).queryByRole("button", { name: "上一张图片" })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole("button", { name: "下一张图片" })).not.toBeInTheDocument();
    expect(within(dialog).queryByLabelText("图片位置指示")).not.toBeInTheDocument();
  });
});
