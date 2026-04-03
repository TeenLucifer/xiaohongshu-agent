import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CodeNode } from "@lexical/code";
import { LinkNode } from "@lexical/link";
import { ListItemNode, ListNode } from "@lexical/list";
import { TRANSFORMERS, $convertFromMarkdownString, $convertToMarkdownString } from "@lexical/markdown";
import { LexicalComposer, type InitialConfigType } from "@lexical/react/LexicalComposer";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { MarkdownShortcutPlugin } from "@lexical/react/LexicalMarkdownShortcutPlugin";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import { mergeRegister } from "@lexical/utils";
import {
  $getSelection,
  $isRangeSelection,
  $setSelection,
  COMMAND_PRIORITY_LOW,
  SELECTION_CHANGE_COMMAND,
  type LexicalEditor,
  type RangeSelection,
} from "lexical";
import type { CopyDraftContent } from "../types/workspace";
import { Button } from "./ui/Button";

const editorTheme = {
  heading: {
    h1: "text-[28px] font-semibold leading-10 text-slate-950",
    h2: "text-[23px] font-semibold leading-9 text-slate-950",
    h3: "text-[19px] font-semibold leading-8 text-slate-900",
  },
  link: "text-blue-600 underline underline-offset-2",
  list: {
    listitem: "my-1",
    nested: {
      listitem: "my-1",
    },
    ol: "list-decimal pl-6",
    ul: "list-disc pl-6",
  },
  paragraph: "min-h-[1.75rem] text-[15px] leading-8 text-slate-800",
  quote: "border-l-2 border-slate-300 pl-4 italic text-slate-600",
  text: {
    bold: "font-semibold",
    code: "rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px]",
    italic: "italic",
  },
};

function escapeMarkdownLine(value: string): string {
  return value.replace(/\n/g, " ");
}

function buildDocumentMarkdown(draft: CopyDraftContent): string {
  const title = draft.title.trim();
  const body = draft.body.trim();
  if (title.length > 0 && body.length > 0) {
    return `# ${escapeMarkdownLine(title)}\n\n${body}`;
  }
  if (title.length > 0) {
    return `# ${escapeMarkdownLine(title)}`;
  }
  return body;
}

function splitDocumentMarkdown(markdown: string): CopyDraftContent {
  const trimmed = markdown.trim();
  if (trimmed.length === 0) {
    return { title: "", body: "" };
  }

  const lines = trimmed.split("\n");
  const firstLine = lines[0]?.trim() ?? "";
  if (firstLine.startsWith("# ") && !firstLine.startsWith("## ")) {
    const title = firstLine.slice(2).trim();
    const body = lines.slice(1).join("\n").replace(/^\s+/, "").trim();
    return { title, body };
  }

  return { title: "", body: trimmed };
}

function createInitialEditorState(markdown: string): (editor: LexicalEditor) => void {
  return (editor: LexicalEditor) => {
    editor.update(() => {
      if (markdown.trim().length > 0) {
        $convertFromMarkdownString(markdown, TRANSFORMERS);
      }
    });
  };
}

function SyncMarkdownPlugin({ markdown }: { markdown: string }): JSX.Element | null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const currentMarkdown = editor.getEditorState().read(() => $convertToMarkdownString(TRANSFORMERS));
    if (currentMarkdown.trim() === markdown.trim()) {
      return;
    }

    editor.update(() => {
      $convertFromMarkdownString(markdown, TRANSFORMERS);
    });
  }, [editor, markdown]);

  return null;
}

function AutoScrollSelectionPlugin(): JSX.Element | null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    let frame = 0;
    const scheduleScroll = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => {
        const selection = window.getSelection();
        if (selection === null || selection.rangeCount === 0) {
          return;
        }
        const node = selection.focusNode;
        const element =
          node instanceof Element ? node : node?.parentElement ?? null;
        if (element !== null && typeof element.scrollIntoView === "function") {
          element.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
      });
    };

    return mergeRegister(
      editor.registerUpdateListener(() => {
        scheduleScroll();
      }),
      editor.registerCommand(
        SELECTION_CHANGE_COMMAND,
        () => {
          scheduleScroll();
          return false;
        },
        COMMAND_PRIORITY_LOW
      ),
      () => {
        window.cancelAnimationFrame(frame);
      }
    );
  }, [editor]);

  return null;
}

function SelectionPolishPlugin({
  onPolishSelection,
}: {
  onPolishSelection: (payload: {
    selectedText: string;
    instruction: string;
    documentMarkdown: string;
  }) => Promise<{ replacementText: string; message: string }>;
}): JSX.Element | null {
  const [editor] = useLexicalComposerContext();
  const [selectionText, setSelectionText] = useState("");
  const [buttonPosition, setButtonPosition] = useState<{ top: number; left: number } | null>(null);
  const [isPromptOpen, setIsPromptOpen] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPolishing, setIsPolishing] = useState(false);
  const selectionRef = useRef<RangeSelection | null>(null);

  const syncSelectionState = useCallback(() => {
      if (isPromptOpen) {
        return;
      }
      const root = editor.getRootElement();
      const domSelection = window.getSelection();
      if (
        root === null ||
        domSelection === null ||
        domSelection.rangeCount === 0 ||
        domSelection.isCollapsed
      ) {
        setSelectionText("");
        setButtonPosition(null);
        if (!isPolishing) {
          setIsPromptOpen(false);
        }
        return;
      }

      const range = domSelection.getRangeAt(0);
      const commonNode = range.commonAncestorContainer;
      const container = commonNode instanceof Element ? commonNode : commonNode.parentElement;
      if (container === null || !root.contains(container)) {
        setSelectionText("");
        setButtonPosition(null);
        if (!isPolishing) {
          setIsPromptOpen(false);
        }
        return;
      }

      editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection) || selection.isCollapsed()) {
          setSelectionText("");
          setButtonPosition(null);
          if (!isPolishing) {
            setIsPromptOpen(false);
          }
          return;
        }

        const nextText = selection.getTextContent().trim();
        if (nextText.length === 0) {
          setSelectionText("");
          setButtonPosition(null);
          if (!isPolishing) {
            setIsPromptOpen(false);
          }
          return;
        }

        selectionRef.current = selection.clone();
        setSelectionText(nextText);
        const rect = range.getBoundingClientRect();
        setButtonPosition({
          top: Math.max(16, rect.top - 48),
          left: Math.max(16, rect.left + rect.width / 2 - 48),
        });
      });
    }, [editor, isPolishing, isPromptOpen]);

  useEffect(() => {
    const root = editor.getRootElement();
    if (root === null) {
      return;
    }
    const handleSelectionChange = () => {
      syncSelectionState();
    };
    return mergeRegister(
      editor.registerCommand(
        SELECTION_CHANGE_COMMAND,
        () => {
          syncSelectionState();
          return false;
        },
        COMMAND_PRIORITY_LOW
      ),
      editor.registerUpdateListener(() => {
        syncSelectionState();
      }),
      () => {
        document.removeEventListener("selectionchange", handleSelectionChange);
        root.removeEventListener("mouseup", handleSelectionChange);
        root.removeEventListener("keyup", handleSelectionChange);
      },
      (() => {
        document.addEventListener("selectionchange", handleSelectionChange);
        root.addEventListener("mouseup", handleSelectionChange);
        root.addEventListener("keyup", handleSelectionChange);
        return () => {};
      })()
    );
  }, [editor, syncSelectionState]);

  async function handlePolishSubmit(): Promise<void> {
    const normalizedInstruction = instruction.trim();
    if (normalizedInstruction.length === 0) {
      setErrorMessage("请输入本次润色要求。");
      return;
    }
    if (selectionRef.current === null || selectionText.trim().length === 0) {
      setErrorMessage("当前没有可润色的选中文本。");
      return;
    }
    setIsPolishing(true);
    setErrorMessage(null);
    try {
      const documentMarkdown = editor.getEditorState().read(() =>
        $convertToMarkdownString(TRANSFORMERS)
      );
      const result = await onPolishSelection({
        selectedText: selectionText,
        instruction: normalizedInstruction,
        documentMarkdown,
      });
      editor.update(() => {
        const storedSelection = selectionRef.current;
        if (storedSelection === null) {
          return;
        }
        $setSelection(storedSelection.clone());
        const currentSelection = $getSelection();
        if ($isRangeSelection(currentSelection)) {
          currentSelection.insertText(result.replacementText);
        }
      });
      setInstruction("");
      setSelectionText("");
      setButtonPosition(null);
      setIsPromptOpen(false);
      selectionRef.current = null;
      window.requestAnimationFrame(() => {
        const selection = window.getSelection();
        if (selection === null || selection.rangeCount === 0) {
          return;
        }
        const node = selection.focusNode;
        const element = node instanceof Element ? node : node?.parentElement ?? null;
        if (element !== null && typeof element.scrollIntoView === "function") {
          element.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
      });
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "AI 润色失败");
    } finally {
      setIsPolishing(false);
    }
  }

  if (buttonPosition === null || selectionText.length === 0) {
    return null;
  }

  return (
    <>
      <div
        className="fixed z-40"
        style={{
          left: `${buttonPosition.left}px`,
          top: `${buttonPosition.top}px`,
        }}
      >
        <Button
          onMouseDown={(event) => {
            event.preventDefault();
          }}
          onClick={() => {
            setIsPromptOpen(true);
            setErrorMessage(null);
          }}
          size="sm"
          type="button"
          variant="primary"
        >
          AI 润色
        </Button>
      </div>

      {isPromptOpen ? (
        <div
          className="fixed z-50 w-[320px] rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl"
          style={{
            left: `${Math.max(16, buttonPosition.left - 80)}px`,
            top: `${buttonPosition.top + 44}px`,
          }}
        >
          <p className="text-sm font-semibold text-slate-900">润色已选内容</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">当前只会替换选中的这段文本，不改其它内容。</p>
          <p className="mt-2 rounded-xl bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-600">
            {selectionText}
          </p>
          <label className="mt-3 block text-xs font-medium text-slate-500" htmlFor="selection-polish-instruction">
            润色要求
          </label>
          <textarea
            className="mt-1 min-h-[88px] w-full rounded-xl border border-slate-200 px-3 py-2 text-sm leading-6 text-slate-800 outline-none transition focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
            id="selection-polish-instruction"
            onChange={(event) => setInstruction(event.target.value)}
            placeholder="例如：更口语一点，保留原意，节奏更短促"
            value={instruction}
          />
          {errorMessage ? (
            <p className="mt-2 text-xs text-rose-500">{errorMessage}</p>
          ) : null}
          <div className="mt-3 flex items-center justify-end gap-2">
            <Button
              onClick={() => {
                setIsPromptOpen(false);
                setInstruction("");
                setErrorMessage(null);
              }}
              size="sm"
              type="button"
              variant="ghost"
            >
              取消
            </Button>
            <Button disabled={isPolishing} onClick={() => void handlePolishSubmit()} size="sm" type="button" variant="primary">
              {isPolishing ? "润色中..." : "开始润色"}
            </Button>
          </div>
        </div>
      ) : null}
    </>
  );
}

export function CopyDraftSummaryPanel({
  copyDraft,
  isSaving = false,
  onChange,
  onPolishSelection,
}: {
  copyDraft: CopyDraftContent;
  isSaving?: boolean;
  onChange: (draft: CopyDraftContent) => void;
  onPolishSelection: (payload: {
    selectedText: string;
    instruction: string;
    documentMarkdown: string;
  }) => Promise<{ replacementText: string; message: string }>;
}): JSX.Element {
  const documentMarkdown = useMemo(() => buildDocumentMarkdown(copyDraft), [copyDraft]);

  const initialConfig = useMemo<InitialConfigType>(
    () => ({
      editorState: createInitialEditorState(documentMarkdown),
      namespace: "copy-draft-editor",
      nodes: [HeadingNode, QuoteNode, ListNode, ListItemNode, CodeNode, LinkNode],
      onError(error: Error) {
        throw error;
      },
      theme: editorTheme,
    }),
    [documentMarkdown]
  );

  return (
    <article>
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-[11px] text-slate-400">{isSaving ? "保存中..." : "已自动保存"}</span>
        <span className="text-[11px] text-slate-400">选中文本后可 AI 润色</span>
      </div>

      <div className="relative">
        <LexicalComposer initialConfig={initialConfig}>
          <ListPlugin />
          <LinkPlugin />
          <HistoryPlugin />
          <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
          <SyncMarkdownPlugin markdown={documentMarkdown} />
          <AutoScrollSelectionPlugin />
          <SelectionPolishPlugin onPolishSelection={onPolishSelection} />
          <OnChangePlugin
            ignoreHistoryMergeTagChange
            ignoreSelectionChange
            onChange={(editorState) => {
              const markdown = editorState.read(() => $convertToMarkdownString(TRANSFORMERS));
              const nextDraft = splitDocumentMarkdown(markdown);
              if (nextDraft.title === copyDraft.title && nextDraft.body === copyDraft.body) {
                return;
              }
              onChange(nextDraft);
            }}
          />
          <RichTextPlugin
            ErrorBoundary={LexicalErrorBoundary}
            contentEditable={
              <ContentEditable
                aria-label="文案正文编辑器"
                className="max-h-[560px] min-h-[380px] overflow-y-auto bg-transparent px-1 py-1 pr-3 text-[15px] leading-8 text-slate-800 outline-none"
              />
            }
            placeholder={
              <div className="pointer-events-none absolute left-1 top-2 text-[15px] leading-8 text-slate-400">
                输入文案内容，例如：
                <br />
                # 通勤穿搭别再乱买了
                <br />
                ## 通勤穿搭公式
              </div>
            }
          />
        </LexicalComposer>
      </div>
    </article>
  );
}
