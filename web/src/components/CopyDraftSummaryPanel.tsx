import type { CopyDraftContent } from "../types/workspace";

export function CopyDraftSummaryPanel({ copyDraft }: { copyDraft: CopyDraftContent }): JSX.Element {
  return (
    <article className="rounded-[20px] bg-slate-50 p-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-400">当前文案</p>
      <h3 className="mt-2 text-sm font-semibold leading-6 text-slate-900">{copyDraft.title}</h3>
      <p className="mt-2 line-clamp-4 text-[13px] leading-6 text-slate-600">{copyDraft.body}</p>
    </article>
  );
}
