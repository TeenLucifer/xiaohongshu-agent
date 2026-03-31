import { Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { MarkdownContent } from "../components/MarkdownContent";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import { listSkills, listTopics, toSkills, toTopicCards } from "../lib/api";
import type { SkillListItem } from "../types/skills";
import type { TopicCard } from "../types/workspace";

export function SkillsPage(): JSX.Element {
  const [topics, setTopics] = useState<TopicCard[]>([]);
  const [skills, setSkills] = useState<SkillListItem[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<SkillListItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    void Promise.all([listTopics(), listSkills()])
      .then(([topicResponse, skillsResponse]) => {
        if (cancelled) {
          return;
        }
        setTopics(toTopicCards(topicResponse.items));
        setSkills(toSkills(skillsResponse.items));
      })
      .catch((cause: unknown) => {
        if (cancelled) {
          return;
        }
        const message = cause instanceof Error ? cause.message : "加载 Skills 失败";
        setError(message);
        setTopics([]);
        setSkills([]);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main
      className="grid h-screen gap-4 pr-4 pl-0"
      data-left-sidebar={isSidebarCollapsed ? "collapsed" : "open"}
      data-testid="skills-shell"
      style={{
        gridTemplateColumns: isSidebarCollapsed ? "80px minmax(0, 1fr)" : "248px minmax(0, 1fr)",
      }}
    >
      <WorkspaceSidebar
        collapsed={isSidebarCollapsed}
        currentTopicId=""
        onToggleCollapse={() => setIsSidebarCollapsed((current) => !current)}
        topics={topics}
      />

      <section className="my-4 h-[calc(100vh-2rem)] overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 shadow-surface">
        <div className="scrollbar-subtle h-full overflow-y-auto px-6 py-8 sm:px-8">
          <div className="mx-auto max-w-5xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.26em] text-slate-400">Skills</p>
                <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950">Skills</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-500">
                  查看当前系统已加载的全部 skills，包括 builtin、workspace 与子 skills。
                </p>
              </div>
              <Badge variant="primary">{skills.length} 项</Badge>
            </div>

            {error ? (
              <Surface className="mt-6 border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700">
                {error}
              </Surface>
            ) : null}

            {isLoading ? (
              <Surface className="mt-6 p-6 text-sm text-slate-500">正在加载 Skills...</Surface>
            ) : null}

            {!isLoading && skills.length === 0 ? (
              <Surface className="mt-6 border border-dashed border-slate-200 bg-slate-50/70 p-8 text-center text-sm text-slate-500">
                当前没有可展示的 Skills。
              </Surface>
            ) : null}

            <div className="mt-8 grid gap-3">
              {skills.map((skill) => (
                <button
                  className="w-full rounded-[24px] border border-slate-200/80 bg-slate-50/70 p-5 text-left transition-colors duration-200 hover:border-slate-300 hover:bg-white"
                  key={`${skill.source}:${skill.location}`}
                  onClick={() => setSelectedSkill(skill)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="truncate text-base font-semibold text-slate-900">{skill.name}</h2>
                        <Badge variant={skill.available ? "primary" : "neutral"}>
                          {skill.available ? "可用" : "缺依赖"}
                        </Badge>
                        <Badge variant="neutral">{skill.source}</Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-500">{skill.description}</p>
                      <p className="mt-3 truncate text-xs text-slate-400">{skill.location}</p>
                    </div>
                    <Sparkles className="mt-1 h-4 w-4 shrink-0 text-slate-400" strokeWidth={1.8} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {selectedSkill ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/28 px-4 py-4">
          <div
            aria-modal="true"
            className="flex max-h-[calc(100vh-2rem)] w-full max-w-3xl flex-col overflow-hidden rounded-[28px] border border-white/60 bg-white shadow-[0_28px_80px_rgba(15,23,42,0.22)]"
            role="dialog"
          >
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200/80 px-6 py-5">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-semibold tracking-tight text-slate-950">
                    {selectedSkill.name}
                  </h2>
                  <Badge variant={selectedSkill.available ? "primary" : "neutral"}>
                    {selectedSkill.available ? "可用" : "缺依赖"}
                  </Badge>
                  <Badge variant="neutral">{selectedSkill.source}</Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-500">{selectedSkill.description}</p>
              </div>

              <Button
                aria-label="关闭 Skills 详情"
                className="shrink-0"
                onClick={() => setSelectedSkill(null)}
                size="icon"
                type="button"
                variant="ghost"
              >
                <X className="h-4 w-4" strokeWidth={1.8} />
              </Button>
            </div>

            <div className="scrollbar-subtle flex-1 overflow-y-auto px-6 py-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <Surface className="rounded-[20px] bg-slate-50/80 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">位置</p>
                  <p className="mt-2 break-all text-sm leading-6 text-slate-700">{selectedSkill.location}</p>
                </Surface>
                <Surface className="rounded-[20px] bg-slate-50/80 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">依赖</p>
                  {selectedSkill.requires.length > 0 ? (
                    <ul className="mt-2 space-y-1 text-sm leading-6 text-slate-700">
                      {selectedSkill.requires.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm leading-6 text-slate-700">无额外缺失依赖。</p>
                  )}
                </Surface>
              </div>

              <Surface className="mt-6 rounded-[24px] bg-slate-50/80 p-5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">正文摘要</p>
                <MarkdownContent
                  className="mt-3 text-sm"
                  content={selectedSkill.contentSummary || "当前没有可展示的正文摘要。"}
                />
              </Surface>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
