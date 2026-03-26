import { StatusBadge } from "./StatusBadge";
import type { WorkspaceSection } from "../types/workspace";

export function WorkspaceSectionCard({ section }: { section: WorkspaceSection }): JSX.Element {
  return (
    <section className="workspace-section">
      <div className="workspace-section-header">
        <h2>{section.title}</h2>
        <StatusBadge status={section.status} />
      </div>
      <p>{section.summary}</p>
    </section>
  );
}
