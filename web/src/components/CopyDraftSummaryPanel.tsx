import { useEffect, useMemo } from "react";
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
import type { LexicalEditor } from "lexical";
import type { CopyDraftContent } from "../types/workspace";

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

export function CopyDraftSummaryPanel({
  copyDraft,
  isSaving = false,
  onChange,
}: {
  copyDraft: CopyDraftContent;
  isSaving?: boolean;
  onChange: (draft: CopyDraftContent) => void;
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
    <article className="rounded-[20px] bg-slate-50 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-400">当前文案</p>
        <span className="text-[11px] text-slate-400">{isSaving ? "保存中..." : "已自动保存"}</span>
      </div>

      <div className="mt-4 rounded-[24px] border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
          <div>
            <p className="text-xs font-medium text-slate-500">Markdown 文案</p>
            <p className="mt-1 text-[11px] text-slate-400">
              输入 <code>#</code>、<code>##</code>、<code>-</code>、<code>&gt;</code> 等语法后会立即格式化
            </p>
          </div>
          <span className="text-[11px] text-slate-400">Shift + Enter 换行</span>
        </div>

        <div className="px-4 py-4">
          <LexicalComposer initialConfig={initialConfig}>
            <ListPlugin />
            <LinkPlugin />
            <HistoryPlugin />
            <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
            <SyncMarkdownPlugin markdown={documentMarkdown} />
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
                  className="min-h-[360px] rounded-[20px] bg-white px-2 py-1 text-[15px] leading-8 text-slate-800 outline-none"
                />
              }
              placeholder={
                <div className="pointer-events-none absolute left-6 top-5 text-[15px] leading-8 text-slate-400">
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
      </div>
    </article>
  );
}
