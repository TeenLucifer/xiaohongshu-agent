import { motion } from "framer-motion";
import { Bot, PencilLine, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "../lib/cn";
import type { ChatMessage, CopyDraftContent } from "../types/workspace";
import { MarkdownContent } from "./MarkdownContent";
import { Button } from "./ui/Button";

export function AgentTimeline({
  copyDraft,
  messages,
  onCopyDraftChange
}: {
  copyDraft: CopyDraftContent | undefined;
  messages: ChatMessage[];
  onCopyDraftChange: (draft: CopyDraftContent) => void;
}): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(copyDraft?.title ?? "");
  const [draftBody, setDraftBody] = useState(copyDraft?.body ?? "");

  useEffect(() => {
    setDraftTitle(copyDraft?.title ?? "");
    setDraftBody(copyDraft?.body ?? "");
  }, [copyDraft]);

  return (
    <ol aria-label="对话消息流" className="grid gap-4">
      {messages.map((message, index) => {
        const isUser = message.role === "user";
        const Icon = isUser ? UserRound : Bot;
        const isCopyMessage = message.type === "copy" && copyDraft !== undefined;

        return (
          <motion.li
            animate={{ opacity: 1, y: 0 }}
            className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}
            initial={{ opacity: 0, y: 12 }}
            key={message.id}
            transition={{ delay: index * 0.04, duration: 0.24, ease: "easeOut" }}
          >
            {!isUser ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white">
                <Icon className="h-4 w-4" strokeWidth={1.9} />
              </div>
            ) : null}

            <div
              className={cn(
                "max-w-[88%] rounded-[24px] border px-4 py-3 shadow-sm",
                isUser
                  ? "border-blue-100 bg-blue-50 text-slate-900"
                  : "border-slate-200 bg-white text-slate-800"
              )}
            >
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <span>{isUser ? "你" : message.agentName ?? "Agent"}</span>
                <span>{message.time}</span>
              </div>

              {isCopyMessage ? (
                <div className="mt-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-[13px] leading-6 text-slate-700">已生成一版完整文案，你可以直接在这里修改。</p>
                    <Button onClick={() => setEditing((current) => !current)} size="sm" type="button" variant="ghost">
                      <PencilLine className="h-3.5 w-3.5" strokeWidth={1.8} />
                      {editing ? "收起" : "编辑"}
                    </Button>
                  </div>

                  {editing ? (
                    <div className="mt-3 grid gap-3">
                      <label className="grid gap-1.5 text-xs text-slate-500">
                        <span>笔记标题</span>
                        <input
                          className="h-11 rounded-2xl border border-slate-200 bg-slate-50 px-3 text-sm text-slate-900 outline-none transition focus:border-blue-300 focus:bg-white"
                          onChange={(event) => {
                            const next = event.target.value;
                            setDraftTitle(next);
                            onCopyDraftChange({ title: next, body: draftBody });
                          }}
                          type="text"
                          value={draftTitle}
                        />
                      </label>
                      <label className="grid gap-1.5 text-xs text-slate-500">
                        <span>笔记正文</span>
                        <textarea
                          className="min-h-44 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm leading-7 text-slate-900 outline-none transition focus:border-blue-300 focus:bg-white"
                          onChange={(event) => {
                            const next = event.target.value;
                            setDraftBody(next);
                            onCopyDraftChange({ title: draftTitle, body: next });
                          }}
                          value={draftBody}
                        />
                      </label>
                    </div>
                  ) : (
                    <div className="mt-3 whitespace-pre-wrap text-[14px] leading-7 text-slate-700">
                      <p className="font-semibold text-slate-900">{copyDraft.title}</p>
                      <p className="mt-3">{copyDraft.body}</p>
                    </div>
                  )}
                </div>
              ) : (
                isUser ? (
                  <p className="mt-2 whitespace-pre-wrap text-[14px] leading-7">{message.text}</p>
                ) : (
                  <MarkdownContent className="mt-2" content={message.text} />
                )
              )}

              {!isUser && (message.toolSummary?.length ?? 0) > 0 ? (
                <details className="mt-3 rounded-2xl border border-slate-200/80 bg-slate-50/80 px-3 py-2">
                  <summary className="cursor-pointer list-none text-[12px] font-medium text-slate-500 [&::-webkit-details-marker]:hidden">
                    工具调用摘要（{message.toolSummary?.length ?? 0}）
                  </summary>
                  <div className="mt-3 grid gap-2">
                    {message.toolSummary?.map((item, itemIndex) => (
                      <article
                        className="rounded-2xl border border-slate-200 bg-white px-3 py-3 text-[12px] leading-6 text-slate-600"
                        key={`${message.id}:tool:${item.name}:${itemIndex}`}
                      >
                        <p className="font-semibold text-slate-900">{item.name}</p>
                        <p className="mt-1 break-words text-slate-500">
                          参数：{item.argumentsSummary}
                        </p>
                        <p className="mt-1 break-words text-slate-500">
                          结果：{item.resultSummary}
                        </p>
                      </article>
                    ))}
                  </div>
                </details>
              ) : null}
            </div>

            {isUser ? (
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-white text-slate-600 shadow-sm ring-1 ring-slate-200">
                <Icon className="h-4 w-4" strokeWidth={1.9} />
              </div>
            ) : null}
          </motion.li>
        );
      })}
    </ol>
  );
}
