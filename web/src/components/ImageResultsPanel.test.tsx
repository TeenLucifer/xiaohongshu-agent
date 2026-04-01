import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ImageResultsPanel } from "./ImageResultsPanel";
import type { GeneratedImageResult } from "../types/workspace";

const results: GeneratedImageResult[] = [
  {
    id: "image-cover-1",
    alt: "文生图封面 1",
    imageUrl: "https://example.com/cover-1.png",
    imagePath: "generated_images/cover-1.png",
    prompt: "请生成封面 1",
    sourceEditorImageIds: ["editor-1"],
    createdAt: "2026-04-01T10:00:00+08:00",
  },
  {
    id: "image-inner-1",
    alt: "文生图内页 1",
    imageUrl: "https://example.com/inner-1.png",
    imagePath: "generated_images/inner-1.png",
    prompt: "请生成内页 1",
    sourceEditorImageIds: ["editor-2"],
    createdAt: "2026-04-01T10:00:01+08:00",
  },
];

describe("ImageResultsPanel", () => {
  it("renders generated images as compact thumbnails without add button", () => {
    render(<ImageResultsPanel results={results} />);

    expect(screen.queryByRole("button", { name: /加入/i })).not.toBeInTheDocument();
    const image = screen.getByRole("img", { name: "文生图封面 1" });
    expect(image.closest(".h-16.w-16")).toBeTruthy();
  });

  it("opens a lightbox for generated images inside the same result list", async () => {
    const user = userEvent.setup();
    render(<ImageResultsPanel results={results} />);

    await user.click(screen.getByRole("img", { name: "文生图封面 1" }));

    const lightbox = screen.getByRole("dialog", { name: "图片预览" });
    expect(within(lightbox).getByRole("img", { name: "文生图封面 1" })).toBeInTheDocument();

    await user.click(within(lightbox).getByRole("button", { name: "下一张预览图片" }));
    expect(within(lightbox).getByRole("img", { name: "文生图内页 1" })).toBeInTheDocument();

    await user.click(within(lightbox).getByRole("button", { name: "关闭图片预览" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "图片预览" })).not.toBeInTheDocument();
    });
  });
});
