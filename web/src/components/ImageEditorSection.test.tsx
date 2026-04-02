import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ImageEditorSection } from "./ImageEditorSection";
import type { EditorImage, MaterialImage } from "../types/workspace";

const materialImages: MaterialImage[] = [
  {
    id: "material-1",
    postId: "post-1",
    postTitle: "测试帖子 1",
    imageUrl: "https://example.com/material-1.png",
    imagePath: "posts/post-1/assets/image-01.png",
    alt: "素材图 1",
  },
  {
    id: "material-2",
    postId: "post-2",
    postTitle: "测试帖子 2",
    imageUrl: "https://example.com/material-2.png",
    imagePath: "posts/post-2/assets/image-01.png",
    alt: "素材图 2",
  },
];

const editorImages: EditorImage[] = [
  {
    id: "editor-1",
    order: 1,
    sourceType: "material",
    sourcePostId: "post-1",
    sourceImageId: "material-1",
    imageUrl: "https://example.com/editor-1.png",
    imagePath: "posts/post-1/assets/image-01.png",
    alt: "编辑图 1",
  },
];

describe("ImageEditorSection", () => {
  it("opens preview for material and editor images, and delete button does not open preview", async () => {
    const user = userEvent.setup();
    const onEditorImagesChange = vi.fn();

    render(
      <ImageEditorSection
        editorImages={editorImages}
        materialImages={materialImages}
        onEditorImagesChange={onEditorImagesChange}
      />
    );

    await user.click(screen.getByRole("img", { name: "素材图 1" }));
    const materialLightbox = screen.getByRole("dialog", { name: "图片预览" });
    expect(within(materialLightbox).getByRole("img", { name: "素材图 1" })).toBeInTheDocument();
    await user.click(within(materialLightbox).getByRole("button", { name: "关闭图片预览" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "图片预览" })).not.toBeInTheDocument();
    });

    await user.click(screen.getByRole("img", { name: "编辑图 1" }));
    const editorLightbox = screen.getByRole("dialog", { name: "图片预览" });
    expect(within(editorLightbox).getByRole("img", { name: "编辑图 1" })).toBeInTheDocument();
    await user.click(within(editorLightbox).getByRole("button", { name: "关闭图片预览" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "图片预览" })).not.toBeInTheDocument();
    });

    const editorCard = screen.getAllByRole("img", { name: "编辑图 1" })[0]?.closest("[role='button']");
    if (!(editorCard instanceof HTMLElement)) {
      throw new Error("editor card not found");
    }

    await user.click(within(editorCard).getByRole("button"));
    expect(onEditorImagesChange).toHaveBeenCalledWith([]);
    expect(screen.queryByRole("dialog", { name: "图片预览" })).not.toBeInTheDocument();
  });

  it("accepts generated-image drag payload and appends it into editor area", () => {
    const onEditorImagesChange = vi.fn();

    render(
      <ImageEditorSection
        editorImages={editorImages}
        materialImages={materialImages}
        onEditorImagesChange={onEditorImagesChange}
      />
    );

    const dropZone = screen.getByText("编辑区 (1)").nextElementSibling;
    if (!(dropZone instanceof HTMLElement)) {
      throw new Error("drop zone not found");
    }

    fireEvent.drop(dropZone, {
      dataTransfer: {
        getData: () =>
          JSON.stringify({
            id: "generated-1",
            sourceType: "generated",
            imageUrl: "https://example.com/generated-1.png",
            imagePath: "generated_images/generated-1.png",
            alt: "生成图 1",
          }),
      },
    });

    expect(onEditorImagesChange).toHaveBeenCalledTimes(1);
    expect(onEditorImagesChange).toHaveBeenCalledWith([
      ...editorImages,
      expect.objectContaining({
        order: 2,
        sourceType: "generated",
        sourceGeneratedImageId: "generated-1",
        imagePath: "generated_images/generated-1.png",
        alt: "生成图 1",
      }),
    ]);
  });

  it("does not append duplicate material image into editor area", () => {
    const onEditorImagesChange = vi.fn();

    render(
      <ImageEditorSection
        editorImages={editorImages}
        materialImages={materialImages}
        onEditorImagesChange={onEditorImagesChange}
      />
    );

    const dropZone = screen.getByText("编辑区 (1)").nextElementSibling;
    if (!(dropZone instanceof HTMLElement)) {
      throw new Error("drop zone not found");
    }

    fireEvent.drop(dropZone, {
      dataTransfer: {
        getData: () => JSON.stringify(materialImages[0]),
      },
    });

    expect(onEditorImagesChange).not.toHaveBeenCalled();
  });

  it("does not append duplicate generated image into editor area", () => {
    const onEditorImagesChange = vi.fn();

    render(
      <ImageEditorSection
        editorImages={[
          ...editorImages,
          {
            id: "editor-2",
            order: 2,
            sourceType: "generated",
            sourceGeneratedImageId: "generated-1",
            imageUrl: "https://example.com/generated-1.png",
            imagePath: "generated_images/generated-1.png",
            alt: "生成图 1",
          },
        ]}
        materialImages={materialImages}
        onEditorImagesChange={onEditorImagesChange}
      />
    );

    const dropZone = screen.getByText("编辑区 (2)").nextElementSibling;
    if (!(dropZone instanceof HTMLElement)) {
      throw new Error("drop zone not found");
    }

    fireEvent.drop(dropZone, {
      dataTransfer: {
        getData: () =>
          JSON.stringify({
            id: "generated-1",
            sourceType: "generated",
            imageUrl: "https://example.com/generated-1.png",
            imagePath: "generated_images/generated-1.png",
            alt: "生成图 1",
          }),
      },
    });

    expect(onEditorImagesChange).not.toHaveBeenCalled();
  });
});
