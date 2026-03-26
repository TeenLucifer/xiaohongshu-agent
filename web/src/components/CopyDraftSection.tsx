import { useState } from "react";
import { StatusBadge } from "./StatusBadge";
import type { CopyDraftContent, WorkspaceSection } from "../types/workspace";

export function CopyDraftSection({
  content,
  section
}: {
  content: CopyDraftContent;
  section: WorkspaceSection;
}): JSX.Element {
  const [title, setTitle] = useState(content.title);
  const [body, setBody] = useState(content.body);

  return (
    <section className="workspace-section">
      <div className="workspace-section-header">
        <h2>{section.title}</h2>
        <StatusBadge status={section.status} />
      </div>
      <p>{section.summary}</p>

      <div className="copy-editor">
        <label className="copy-field">
          <span>笔记标题</span>
          <input onChange={(event) => setTitle(event.target.value)} type="text" value={title} />
        </label>

        <label className="copy-field">
          <span>笔记正文</span>
          <textarea onChange={(event) => setBody(event.target.value)} rows={10} value={body} />
        </label>
      </div>
    </section>
  );
}
