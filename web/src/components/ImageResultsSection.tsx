import { StatusBadge } from "./StatusBadge";
import type { ImageTaskGroup, WorkspaceSection } from "../types/workspace";

export function ImageResultsSection({
  groups,
  section
}: {
  groups: ImageTaskGroup[];
  section: WorkspaceSection;
}): JSX.Element {
  return (
    <section className="workspace-section">
      <div className="workspace-section-header">
        <h2>{section.title}</h2>
        <StatusBadge status={section.status} />
      </div>
      <p>{section.summary}</p>

      <div className="image-task-stack">
        {groups.map((group) => (
          <div className="image-task-group" key={group.id}>
            <div className="image-task-group-header">
              <h3>{group.title}</h3>
              <span>{group.summary}</span>
            </div>
            <div className="image-task-grid">
              {group.images.map((image) => (
                <figure className="image-task-card" key={image.id}>
                  <img alt={image.alt} src={image.imageUrl} />
                  <figcaption>{image.kind === "cover" ? "封面候选图" : "内页候选图"}</figcaption>
                </figure>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
