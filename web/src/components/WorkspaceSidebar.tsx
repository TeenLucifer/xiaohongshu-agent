import { Clock3, FolderKanban, Settings, Sparkles } from "lucide-react";
import { NavLink } from "react-router-dom";
import { mockTopics } from "../data/mockTopics";
import { cn } from "../lib/cn";

const navigationItems = [
  { id: "workspace", label: "当前话题", icon: FolderKanban },
  { id: "history", label: "历史记录", icon: Clock3 },
  { id: "skills", label: "Skills", icon: Sparkles },
  { id: "settings", label: "设置", icon: Settings }
];

export function WorkspaceSidebar({ currentTopicId }: { currentTopicId: string }): JSX.Element {
  return (
    <aside
      aria-label="主导航"
      className="scrollbar-subtle flex h-[calc(100vh-2rem)] flex-col overflow-y-auto rounded-[28px] border border-slate-200/80 bg-slate-50/90 px-4 py-5 shadow-surface"
    >
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white">
          XH
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">小红书运营台</p>
          <p className="text-xs text-slate-500">Topic Workspace</p>
        </div>
      </div>

      <nav className="grid gap-1.5">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const active = item.id === "workspace";

          return (
            <button
              className={cn(
                "flex h-11 items-center gap-3 rounded-2xl px-3 text-left text-sm transition-colors duration-200",
                active ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:bg-white/70 hover:text-slate-900"
              )}
              key={item.id}
              type="button"
            >
              <Icon className="h-4 w-4" strokeWidth={1.75} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-8">
        <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">话题切换</p>
        <div className="mt-3 grid gap-2">
          {mockTopics.map((topic) => (
            <NavLink
              className={({ isActive }) =>
                cn(
                  "rounded-2xl border px-3.5 py-3 transition-colors duration-200",
                  isActive || topic.id === currentTopicId
                    ? "border-slate-200 bg-white text-slate-900 shadow-sm"
                    : "border-transparent bg-transparent text-slate-500 hover:border-slate-200/80 hover:bg-white/70 hover:text-slate-900"
                )
              }
              key={topic.id}
              to={`/topics/${topic.id}`}
            >
              <p className="truncate text-sm font-medium">{topic.title}</p>
              <p className="mt-1 text-xs text-slate-400">{topic.updatedAt}</p>
            </NavLink>
          ))}
        </div>
      </div>
    </aside>
  );
}
