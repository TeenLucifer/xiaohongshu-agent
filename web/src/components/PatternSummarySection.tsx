import { StatusBadge } from "./StatusBadge";
import { MarkdownContent } from "./MarkdownContent";
import type { PatternSummaryContent, WorkspaceSection } from "../types/workspace";

function buildPatternSummaryMarkdown(content: PatternSummaryContent): string {
  const sections: string[] = [];

  // 总结文本（如果有）
  if ((content.summaryText ?? "").trim().length > 0) {
    sections.push("## 总结", "", content.summaryText ?? "");
  }

  // 标题模式
  if (content.titlePatterns.length > 0) {
    sections.push("## 标题模式", "", ...content.titlePatterns.map((pattern) => `- ${pattern}`));
  }

  // 正文结构
  if (content.bodyPatterns.length > 0) {
    sections.push("## 正文结构", "", ...content.bodyPatterns.map((pattern) => `- ${pattern}`));
  }

  // 图片模式
  if (content.imagePatterns.length > 0) {
    sections.push("## 图片模式", "", ...content.imagePatterns.map((pattern) => `- ${pattern}`));
  }

  // 图片质量评价
  if ((content.imageQualityNotes ?? "").trim().length > 0) {
    sections.push("## 图片质量评价", "", content.imageQualityNotes ?? "");
  }

  // 高频关键词
  if (content.keywords.length > 0) {
    sections.push(
      "## 高频关键词",
      "",
      content.keywords.map((keyword) => `- \`${keyword}\``).join("\n")
    );
  }

  return sections.join("\n");
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
