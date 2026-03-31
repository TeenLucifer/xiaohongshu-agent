import { StatusBadge } from "./StatusBadge";
import { MarkdownContent } from "./MarkdownContent";
import type { PatternSummaryContent, WorkspaceSection } from "../types/workspace";

function buildPatternSummaryMarkdown(content: PatternSummaryContent): string {
  if ((content.summaryText ?? "").trim().length > 0) {
    return content.summaryText ?? "";
  }

  const titleSection =
    content.titlePatterns.length > 0
      ? ["## 标题模式", "", ...content.titlePatterns.map((pattern) => `- ${pattern}`)].join("\n")
      : "";
  const bodySection =
    content.bodyPatterns.length > 0
      ? ["## 正文结构", "", ...content.bodyPatterns.map((pattern) => `- ${pattern}`)].join("\n")
      : "";
  const keywordSection =
    content.keywords.length > 0
      ? [
          "## 高频关键词",
          "",
          content.keywords.map((keyword) => `- \`${keyword}\``).join("\n"),
        ].join("\n")
      : "";

  return [titleSection, bodySection, keywordSection].filter((section) => section.length > 0).join("\n\n");
}

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

      <div className="content-panel">
        <MarkdownContent content={buildPatternSummaryMarkdown(content)} />
      </div>
    </section>
  );
}
