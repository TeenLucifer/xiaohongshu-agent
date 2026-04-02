import { MessageSquarePlus, PanelLeftClose, Settings, Sparkles } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../lib/cn";
import type { TopicCard } from "../types/workspace";
import { Button } from "./ui/Button";

const navigationItems = [
  { id: "new-topic", label: "新话题", icon: MessageSquarePlus, to: "/" },
  { id: "skills", label: "Skills", icon: Sparkles, to: "/skills" },
  { id: "settings", label: "设置", icon: Settings }
];

export function WorkspaceSidebar({
  collapsed,
  currentTopicId,
  topics,
  onToggleCollapse
}: {
  collapsed: boolean;
  currentTopicId: string;
  topics: TopicCard[];
  onToggleCollapse: () => void;
}): JSX.Element {
  const location = useLocation();

  return (
    <aside
      aria-label="主导航"
      className={cn(
        "scrollbar-subtle flex h-screen flex-col border-r border-slate-200/80 bg-slate-50/90 px-3 py-5",
        collapsed ? "overflow-hidden" : "overflow-y-auto"
      )}
      data-state={collapsed ? "collapsed" : "open"}
      data-testid="workspace-sidebar"
    >
      <div className="mb-6 grid grid-cols-[44px_minmax(0,1fr)] items-center gap-3">
        {collapsed ? (
          <button
            aria-label="展开侧边栏"
            className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white transition-transform duration-200 hover:scale-[1.03]"
            onClick={onToggleCollapse}
            type="button"
          >
            XH
          </button>
        ) : (
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white">
            XH
          </div>
        )}

        <div
          aria-hidden={collapsed}
          className={cn(
            "min-w-0 overflow-hidden transition-all duration-300",
            collapsed ? "max-w-0 opacity-0" : "max-w-[180px] opacity-100"
          )}
        >
          <div className="flex min-w-0 items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">小红书运营台</p>
            </div>
            <Button aria-label="收起侧边栏" onClick={onToggleCollapse} size="icon" type="button" variant="ghost">
              <PanelLeftClose className="h-4 w-4" strokeWidth={1.8} />
            </Button>
          </div>
        </div>
      </div>

      <nav className="grid justify-items-start gap-1.5">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const active =
            item.id === "new-topic"
              ? location.pathname === "/" || location.pathname === "/topics"
              : item.id === "skills"
                ? location.pathname === "/skills"
                : false;
          const classes = cn(
            "grid w-full grid-cols-[44px_minmax(0,1fr)] items-center rounded-2xl text-left text-sm transition-colors duration-300",
            "h-11",
            active ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:bg-white/70 hover:text-slate-900"
          );

          const content = (
            <>
              <span className="flex h-10 w-11 items-center justify-center">
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
              </span>
              <span
                aria-hidden={collapsed}
                className={cn(
                  "overflow-hidden whitespace-nowrap transition-all duration-300",
                  collapsed ? "max-w-0 opacity-0" : "max-w-[120px] opacity-100"
                )}
              >
                <span className="block truncate pr-3">{item.label}</span>
              </span>
            </>
          );

          if (item.to) {
            return (
              <NavLink aria-label={item.label} className={classes} key={item.id} to={item.to}>
                {content}
              </NavLink>
            );
          }

          return (
            <button
              aria-label={item.label}
              className={classes}
              key={item.id}
              type="button"
            >
              {content}
            </button>
          );
        })}
      </nav>

      <div
        aria-hidden={collapsed}
        className={cn("mt-8 overflow-hidden transition-all duration-300", collapsed ? "pointer-events-none max-h-0 opacity-0" : "max-h-[520px] opacity-100")}
        hidden={collapsed}
      >
        <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">话题切换</p>
        <div className="mt-3 grid gap-2">
          {topics.map((topic) => (
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
