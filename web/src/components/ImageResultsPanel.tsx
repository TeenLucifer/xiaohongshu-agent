import type { ImageTaskGroup } from "../types/workspace";

export function ImageResultsPanel({ groups }: { groups: ImageTaskGroup[] }): JSX.Element {
  if (groups.length === 0) {
    return <p className="text-sm text-slate-500">空状态</p>;
  }

  return (
    <div className="grid gap-3">
      {groups.map((group) => (
        <article className="rounded-[20px] bg-slate-50 p-3" key={group.id}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">{group.title}</h3>
              <p className="mt-1 text-xs leading-5 text-slate-500">{group.summary}</p>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2">
            {group.images.map((image) => (
              <figure className="overflow-hidden rounded-2xl border border-slate-200 bg-white" key={image.id}>
                <img alt={image.alt} className="aspect-[3/4] h-full w-full object-cover" src={image.imageUrl} />
              </figure>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
