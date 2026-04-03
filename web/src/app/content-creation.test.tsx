import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  await screen.findByTestId("workspace-main-panel");
  return view;
}

function findFirstTextNode(node: Node | null): Text | null {
  if (node instanceof Text) {
    return node;
  }
  if (node === null) {
    return null;
  }
  for (const child of Array.from(node.childNodes)) {
    const match = findFirstTextNode(child);
    if (match !== null) {
      return match;
    }
  }
  return null;
}

describe("content creation feature", () => {
  it("renders summary in the main chat column and keeps structured content in the right workspace", async () => {
    const user = userEvent.setup();
    await renderWorkspace();
    await user.click(screen.getByRole("button", { name: "对话" }));

    expect((await screen.findAllByText("标题会先切通勤场景")).length).toBeGreaterThan(0);
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

    expect(within(copyGroup).queryByText("当前文案")).not.toBeInTheDocument();
    expect(within(copyGroup).queryByText("Markdown 文案")).not.toBeInTheDocument();
    expect(within(copyGroup).getByLabelText("文案正文编辑器")).toBeInTheDocument();
    expect(within(copyGroup).getByRole("button", { name: "重新生成文案" })).toBeInTheDocument();
  });

  it("shows copy summary and grouped images in the right workspace", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    const candidateToggle = screen.getByRole("button", { name: /搜索结果/ });
    const candidateGroup = candidateToggle.closest("section");
    if (!(candidateGroup instanceof HTMLElement)) {
      throw new Error("candidate group not found");
    }
    expect(within(candidateGroup).getByRole("button", { name: "重新生成总结" })).toBeInTheDocument();
    expect(within(candidateGroup).getByPlaceholderText("输入你想继续让agent处理的内容...")).toBeInTheDocument();
    await user.click(within(candidateGroup).getByRole("button", { name: "展开总结" }));
    expect(within(candidateGroup).getByText("标题模式")).toBeInTheDocument();
    expect(within(candidateGroup).getByText("高频关键词")).toBeInTheDocument();

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);
    expect(within(copyGroup).queryByText("当前文案")).not.toBeInTheDocument();
    expect(within(copyGroup).getByLabelText("文案正文编辑器")).toBeInTheDocument();

    const imageToggle = screen.getByRole("button", { name: "展开图片" });
    const imageGroup = imageToggle.closest("section");
    if (!(imageGroup instanceof HTMLElement)) {
      throw new Error("image group not found");
    }
    await user.click(imageToggle);
    expect(within(imageGroup).getByText(/^素材图片 \(\d+\)$/)).toBeInTheDocument();
    expect(within(imageGroup).getByText(/^编辑区 \(\d+\)$/)).toBeInTheDocument();
    expect(within(imageGroup).getByPlaceholderText("输入你想继续让agent处理的内容...")).toBeInTheDocument();
    expect(within(imageGroup).getByLabelText("图片局部对话输入框").tagName).toBe("TEXTAREA");
    const editorLabel = within(imageGroup).getByText(/^编辑区 \(\d+\)$/);
    const generatedLabel = within(imageGroup).getByText(/^生成结果 \(\d+\)$/);
    const imageComposer = within(imageGroup).getByLabelText("图片局部对话输入框");
    const editorPosition = editorLabel.compareDocumentPosition(imageComposer);
    const generatedPosition = imageComposer.compareDocumentPosition(generatedLabel);
    expect(editorPosition & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(generatedPosition & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
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

    await screen.findByTestId("workspace-main-panel");

    const candidateToggle = screen.getByRole("button", { name: /搜索结果/ });
    const candidateGroup = candidateToggle.closest("section");
    if (!(candidateGroup instanceof HTMLElement)) {
      throw new Error("candidate group not found");
    }
    await user.click(within(candidateGroup).getByRole("button", { name: "生成总结" }));
    expect(screen.getByRole("button", { name: "创作" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "对话" }));
    expect(
      await screen.findByText("请基于当前保留帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。")
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "创作" }));
    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);
    await user.click(within(copyGroup).getByRole("button", { name: "生成文案" }));
    expect(screen.getByRole("button", { name: "创作" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "对话" }));
    expect(
      await screen.findByText("请基于当前保留帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。")
    ).toBeInTheDocument();
  });

  it("supports whiteboard-style markdown editing in the copy draft panel", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);

    expect(await within(copyGroup).findByRole("heading", { level: 1, name: "通勤穿搭别再乱买了，4 件基础单品就够用" })).toBeInTheDocument();
    const editor = within(copyGroup).getByLabelText("文案正文编辑器");
    await user.click(editor);
    await user.type(editor, "补一段新的正文");

    expect(await within(copyGroup).findByText("已自动保存")).toBeInTheDocument();
    expect(within(copyGroup).getByText("选中文本后可 AI 润色")).toBeInTheDocument();
    expect(editor).toHaveClass("overflow-y-auto");
  });

  it("removes the old materials section and uploads local images inside the image section", async () => {
    const user = userEvent.setup();
    const { container } = await renderWorkspace();

    expect(screen.queryByRole("button", { name: "展开素材" })).not.toBeInTheDocument();

    const imageToggle = screen.getByRole("button", { name: "展开图片" });
    const imageGroup = imageToggle.closest("section");
    if (!(imageGroup instanceof HTMLElement)) {
      throw new Error("image group not found");
    }
    await user.click(imageToggle);
    expect(within(imageGroup).getByRole("button", { name: "上传图片" })).toBeInTheDocument();

    const fileInput = container.querySelector("input[type='file']");
    if (!(fileInput instanceof HTMLInputElement)) {
      throw new Error("file input not found");
    }
    const file = new File(["mock-image"], "reference.png", { type: "image/png" });
    await user.upload(fileInput, file);

    expect(await within(imageGroup).findByRole("img", { name: "上传素材" })).toBeInTheDocument();
  });

  it("keeps the polish prompt open after focusing its input", async () => {
    const user = userEvent.setup();
    await renderWorkspace();

    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);

    const heading = await within(copyGroup).findByRole("heading", {
      level: 1,
      name: "通勤穿搭别再乱买了，4 件基础单品就够用",
    });
    const textNode = findFirstTextNode(heading);
    if (textNode === null) {
      throw new Error("heading text node not found");
    }

    const range = document.createRange();
    range.setStart(textNode, 0);
    range.setEnd(textNode, 6);
    const selection = window.getSelection();
    if (selection === null) {
      throw new Error("selection not available");
    }
    selection.removeAllRanges();
    selection.addRange(range);
    document.dispatchEvent(new Event("selectionchange"));

    const polishButton = await screen.findByRole("button", { name: "AI 润色" });
    await user.click(polishButton);

    const instructionInput = await screen.findByLabelText("润色要求");
    await user.click(instructionInput);

    expect(screen.getByText("润色已选内容")).toBeInTheDocument();
    expect(screen.getByLabelText("润色要求")).toBeInTheDocument();

    fireEvent.mouseUp(heading);
  });

  it("shows an editable copy draft panel even when no draft exists yet", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter
        future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
        initialEntries={["/topics/topic-small-rental"]}
      >
        <AppRoutes />
      </MemoryRouter>
    );

    await screen.findByTestId("workspace-main-panel");
    const copyToggle = screen.getByRole("button", { name: "展开文案" });
    const copyGroup = copyToggle.closest("section");
    if (!(copyGroup instanceof HTMLElement)) {
      throw new Error("copy group not found");
    }
    await user.click(copyToggle);

    expect(within(copyGroup).queryByText("当前文案")).not.toBeInTheDocument();
    expect(within(copyGroup).getByLabelText("文案正文编辑器")).toBeInTheDocument();
  });

  it("sends scoped messages from the search and image sections while staying on the current tab", async () => {
    const user = userEvent.setup();
    const originalFetch = globalThis.fetch;
    const pendingStreamResolvers: Array<() => void> = [];
    globalThis.fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url =
        typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      const path = new URL(url, "http://127.0.0.1:8000").pathname;
      if (path.endsWith("/runs/stream")) {
        return new Promise<Response>((resolve) => {
          pendingStreamResolvers.push(() => {
            void Promise.resolve(originalFetch(input, init)).then(resolve);
          });
        });
      }
      return originalFetch(input, init);
    }) as typeof fetch;
    try {
      await renderWorkspace();

      const candidateToggle = screen.getByRole("button", { name: /搜索结果/ });
      const candidateGroup = candidateToggle.closest("section");
      if (!(candidateGroup instanceof HTMLElement)) {
        throw new Error("candidate group not found");
      }
      await user.type(
        within(candidateGroup).getByLabelText("搜索结果局部对话输入框"),
        "继续搜一些类似内容{shift>}{enter}{/shift}并且把标题方向扩一轮"
      );
      expect(within(candidateGroup).getByLabelText("搜索结果局部对话输入框").tagName).toBe("TEXTAREA");
      await user.click(within(candidateGroup).getByRole("button", { name: "发送" }));
      expect(within(candidateGroup).getByLabelText("搜索结果局部对话输入框")).toHaveValue(
        "正在搜索..."
      );
      expect(within(candidateGroup).getByLabelText("搜索结果局部对话输入框")).toBeDisabled();
      expect(screen.getByRole("button", { name: "创作" })).toHaveAttribute("aria-pressed", "true");
      pendingStreamResolvers.shift()?.();
      await waitFor(() =>
        expect(within(candidateGroup).getByLabelText("搜索结果局部对话输入框")).toHaveValue("")
      );

      await user.click(screen.getByRole("button", { name: "对话" }));
      expect((await screen.findAllByText(/继续搜一些类似内容/)).length).toBeGreaterThan(0);

      await user.click(screen.getByRole("button", { name: "创作" }));
      const imageToggle = screen.getByRole("button", { name: "展开图片" });
      const imageGroup = imageToggle.closest("section");
      if (!(imageGroup instanceof HTMLElement)) {
        throw new Error("image group not found");
      }
      await user.click(imageToggle);
      await user.type(
        within(imageGroup).getByLabelText("图片局部对话输入框"),
        "参考1号图再生成一张{shift>}{enter}{/shift}主体换成更轻一点的构图"
      );
      expect(within(imageGroup).getByLabelText("图片局部对话输入框").tagName).toBe("TEXTAREA");
      await user.click(within(imageGroup).getByRole("button", { name: "发送" }));
      expect(within(imageGroup).getByLabelText("图片局部对话输入框")).toHaveValue(
        "图片正在生成..."
      );
      expect(within(imageGroup).getByLabelText("图片局部对话输入框")).toBeDisabled();
      expect(screen.getByRole("button", { name: "创作" })).toHaveAttribute("aria-pressed", "true");
      pendingStreamResolvers.shift()?.();
      await waitFor(() =>
        expect(within(imageGroup).getByLabelText("图片局部对话输入框")).toHaveValue("")
      );

      await user.click(screen.getByRole("button", { name: "对话" }));
      expect((await screen.findAllByText(/参考1号图再生成一张/)).length).toBeGreaterThan(0);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
