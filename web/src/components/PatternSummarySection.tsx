import { StatusBadge } from "./StatusBadge";
import type { PatternSummaryContent, WorkspaceSection } from "../types/workspace";

export function PatternSummarySection({
  content,
  section
}: {
  content: PatternSummaryContent;
  section: WorkspaceSection;
}): JSX.Element {
  return (
    <section className="workspace-section">
      <div className="workspace-section-header">
        <h2>{section.title}</h2>
        <StatusBadge status={section.status} />
      </div>
      <p>{section.summary}</p>

      <div className="content-grid">
        <div className="content-panel">
          <h3>标题模式</h3>
          <ul>
            {content.titlePatterns.map((pattern) => (
              <li key={pattern}>{pattern}</li>
            ))}
          </ul>
        </div>
        <div className="content-panel">
          <h3>正文结构</h3>
          <ul>
            {content.bodyPatterns.map((pattern) => (
              <li key={pattern}>{pattern}</li>
            ))}
          </ul>
        </div>
        <div className="content-panel">
          <h3>高频关键词</h3>
          <div className="keyword-list">
            {content.keywords.map((keyword) => (
              <span className="keyword-pill" key={keyword}>
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
