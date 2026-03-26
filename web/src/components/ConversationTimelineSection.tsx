import { useState } from "react";
import { StatusBadge } from "./StatusBadge";
import type { ConversationEntry, ConversationStatus, WorkspaceSection } from "../types/workspace";

const conversationStatusLabelMap: Record<ConversationStatus, string> = {
  completed: "已完成",
  running: "运行中",
  failed: "失败"
};

export function ConversationTimelineSection({
  entries,
  section
}: {
  entries: ConversationEntry[];
  section: WorkspaceSection;
}): JSX.Element {
  const [expandedEntryIds, setExpandedEntryIds] = useState<string[]>([]);

  function toggleExpanded(entryId: string): void {
    setExpandedEntryIds((current) => {
      if (current.includes(entryId)) {
        return current.filter((id) => id !== entryId);
      }

      return [...current, entryId];
    });
  }

  return (
    <section className="workspace-section">
      <div className="workspace-section-header">
        <h2>{section.title}</h2>
        <StatusBadge status={section.status} />
      </div>
      <p>{section.summary}</p>

      <ol aria-label="Agent 会话时间线" className="conversation-list">
        {entries.map((entry) => {
          const expanded = expandedEntryIds.includes(entry.id);

          return (
            <li className="conversation-item" key={entry.id}>
              <div className="conversation-item-topline">
                <span className="conversation-time">{entry.time}</span>
                <span className={`conversation-status conversation-status-${entry.status}`}>
                  {conversationStatusLabelMap[entry.status]}
                </span>
              </div>

              <div className="conversation-item-body">
                <h3>{entry.agentName}</h3>
                <div className="conversation-summary-block">
                  <strong>输入摘要</strong>
                  <p>{entry.inputSummary}</p>
                </div>
                <div className="conversation-summary-block">
                  <strong>输出摘要</strong>
                  <p>{entry.outputSummary}</p>
                </div>
              </div>

              <button className="conversation-toggle" onClick={() => toggleExpanded(entry.id)} type="button">
                {expanded ? "收起详细日志" : "查看详细日志"}
              </button>

              {expanded ? (
                <div className="conversation-log-panel">
                  <h4>详细日志</h4>
                  <ul>
                    {entry.detailLogs.map((log) => (
                      <li key={log}>{log}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
