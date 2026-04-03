import { ArrowRight, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import { createTopic, deleteTopic, listTopics, toTopicCards } from "../lib/api";
import type { TopicCard } from "../types/workspace";

function formatRelativeTime(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return "最近更新";
  }

  const diffMs = Date.now() - timestamp;
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diffMs < minute) {
    return "刚刚更新";
  }
  if (diffMs < hour) {
    return `${Math.max(1, Math.floor(diffMs / minute))} 分钟前`;
  }
  if (diffMs < day) {
    return `${Math.max(1, Math.floor(diffMs / hour))} 小时前`;
  }
  if (diffMs < day * 7) {
    return `${Math.max(1, Math.floor(diffMs / day))} 天前`;
  }
  return "最近更新";
}

export function TopicListPage(): JSX.Element {
  const navigate = useNavigate();
  const [topics, setTopics] = useState<TopicCard[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [title, setTitle] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    void listTopics()
      .then((response) => {
        if (!cancelled) {
          setTopics(toTopicCards(response.items));
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          const message = cause instanceof Error ? cause.message : "加载话题列表失败";
          setError(message);
          setTopics([]);
        }
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

  async function handleCreate(): Promise<void> {
    const topicTitle = title.trim();
    if (topicTitle.length === 0 || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await createTopic(topicTitle);
      navigate(`/topics/${created.topic_id}`);
    } catch (cause: unknown) {
      const message = cause instanceof Error ? cause.message : "创建话题失败";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(topicId: string): Promise<void> {
    if (deletingId !== null) {
      return;
    }
    setDeletingId(topicId);
    setError(null);
    try {
      await deleteTopic(topicId);
      setTopics((current) => current.filter((topic) => topic.id !== topicId));
    } catch (cause: unknown) {
      const message = cause instanceof Error ? cause.message : "删除话题失败";
      setError(message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main
      className="grid h-screen gap-4 pr-4 pl-0"
      data-left-sidebar={isSidebarCollapsed ? "collapsed" : "open"}
      data-testid="home-shell"
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

      <section className="my-4 h-[calc(100vh-2rem)] overflow-hidden rounded-[28px] border border-slate-200/80 bg-slate-50 shadow-surface">
        <div className="scrollbar-subtle h-full overflow-y-auto px-6 py-10 text-slate-900 sm:px-10">
          <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col">
            <section className="flex flex-1 items-center justify-center py-8">
              <div className="w-full max-w-3xl text-center">
                <div className="mx-auto max-w-[44rem] rounded-[36px] border border-slate-200/90 bg-white px-8 py-10 shadow-[0_20px_44px_rgba(148,163,184,0.12),0_8px_18px_rgba(15,23,42,0.04)] sm:px-12 sm:py-12">
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">小红书运营台</p>
                  <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">新话题</h1>
                  <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-500 sm:text-base">
                    输入一句明确的话题标题，立即开始新的运营工作。
                  </p>

                  <form
                    className="mx-auto mt-10 w-full max-w-[36rem]"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void handleCreate();
                    }}
                  >
                    <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 shadow-[0_12px_24px_rgba(148,163,184,0.1),0_4px_10px_rgba(15,23,42,0.03)]">
                      <label className="sr-only" htmlFor="topic-title">
                        话题标题
                      </label>
                      <input
                        autoComplete="off"
                        className="h-11 flex-1 border-0 bg-transparent px-3 text-[15px] leading-6 text-slate-900 outline-none placeholder:text-slate-400"
                        id="topic-title"
                        onChange={(event) => setTitle(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            void handleCreate();
                          }
                        }}
                        placeholder="例如：春季通勤穿搭、OpenClaw 热门帖子分析"
                        type="text"
                        value={title}
                      />
                      <Button
                        aria-label="创建话题"
                        className="h-9 w-9 shrink-0 rounded-full border-slate-200 bg-white px-0 text-blue-600 shadow-sm hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                        disabled={isSubmitting}
                        type="submit"
                        variant="secondary"
                      >
                        <Plus className="h-3.5 w-3.5" strokeWidth={2} />
                      </Button>
                    </div>
                    {error ? <p className="mt-3 text-left text-sm text-rose-700">{error}</p> : null}
                  </form>
                </div>
              </div>
            </section>

            <section className="pb-4" aria-label="最近话题">
              <div className="mb-3 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-sm font-medium text-slate-700">继续最近话题</h2>
                </div>
                {isLoading ? <p className="text-xs text-slate-400">正在加载...</p> : null}
              </div>

              {!isLoading && topics.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-5 text-sm text-slate-500">
                  当前还没有历史话题，从上方创建你的第一个话题。
                </div>
              ) : null}

              {topics.length > 0 ? (
                <div className="scrollbar-subtle -mx-1 overflow-x-auto px-1 pb-2" data-testid="recent-topics-rail">
                  <div className="flex min-w-max gap-3">
                    {topics.map((topic) => {
                      const deleting = deletingId === topic.id;
                      return (
                        <Surface
                          className="group relative w-[144px] shrink-0 overflow-hidden rounded-[20px] border border-slate-200 bg-white p-0 shadow-[0_10px_22px_rgba(15,23,42,0.05)]"
                          key={topic.id}
                        >
                          <button
                            aria-label={`删除${topic.title}`}
                            className="absolute top-2 right-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-white/92 text-slate-300 opacity-0 shadow-sm transition-all duration-200 group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
                            disabled={deleting}
                            onClick={() => void handleDelete(topic.id)}
                            type="button"
                          >
                            <Trash2 className="h-3.5 w-3.5" strokeWidth={1.8} />
                          </button>

                          <Link
                            aria-label={`进入${topic.title}`}
                            className="relative block aspect-[3/4] outline-none transition-opacity duration-200 hover:opacity-90"
                            to={`/topics/${topic.id}`}
                          >
                            {topic.previewImageUrl ? (
                              <img
                                alt=""
                                className="pointer-events-none absolute inset-0 h-full w-full object-cover"
                                src={topic.previewImageUrl}
                              />
                            ) : (
                              <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.98)_46%,rgba(226,232,240,0.96)_100%)]" />
                            )}
                            <div
                              className={`pointer-events-none absolute inset-0 ${
                                topic.previewImageUrl
                                  ? "bg-[linear-gradient(180deg,rgba(15,23,42,0.08),rgba(15,23,42,0.16)_42%,rgba(15,23,42,0.72)_100%)]"
                                  : "bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.08)_42%,rgba(255,255,255,0.56)_100%)]"
                              }`}
                            />
                            <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 p-3">
                              <div className="min-w-0">
                                <p
                                  className={`line-clamp-4 text-sm font-semibold leading-5 ${
                                    topic.previewImageUrl ? "text-white" : "text-slate-900"
                                  }`}
                                >
                                  {topic.title}
                                </p>
                                <p
                                  className={`mt-2 truncate text-xs ${
                                    topic.previewImageUrl ? "text-white/82" : "text-slate-500"
                                  }`}
                                >
                                  {formatRelativeTime(topic.updatedAt)}
                                </p>
                              </div>
                              <span
                                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                                  topic.previewImageUrl
                                    ? "bg-white/18 text-white"
                                    : "bg-white/78 text-slate-500"
                                }`}
                              >
                                <ArrowRight className="h-3.5 w-3.5" strokeWidth={1.8} />
                              </span>
                            </div>
                          </Link>
                        </Surface>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
