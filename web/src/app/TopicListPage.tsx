import { ArrowRight, MessageSquarePlus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import { createTopic, deleteTopic, listTopics, toTopicCards } from "../lib/api";
import type { TopicCard } from "../types/workspace";

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

      <section className="my-4 h-[calc(100vh-2rem)] overflow-hidden rounded-[28px] border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.92),_rgba(241,245,249,0.95)_45%,_rgba(226,232,240,0.85)_100%)] shadow-surface">
        <div className="scrollbar-subtle h-full overflow-y-auto px-6 py-10 text-slate-900 sm:px-10">
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col justify-center">
            <section className="mx-auto w-full max-w-2xl text-center">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">小红书运营台</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">新话题</h1>
              <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-500 sm:text-base">
                输入一句明确的话题标题，立即开始新的运营工作。
              </p>

              <Surface className="mt-10 rounded-[28px] border border-white/70 bg-white/90 p-4 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
                <form
                  className="flex flex-col gap-3 sm:flex-row sm:items-center"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreate();
                  }}
                >
                  <label className="sr-only" htmlFor="topic-title">
                    话题标题
                  </label>
                  <input
                    className="h-14 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-5 text-base text-slate-900 outline-none transition-colors duration-200 placeholder:text-slate-400 focus:border-slate-300 focus:bg-white"
                    id="topic-title"
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="例如：春季通勤穿搭、OpenClaw 热门帖子分析"
                    type="text"
                    value={title}
                  />
                  <Button
                    className="h-14 rounded-2xl px-6 text-sm"
                    disabled={isSubmitting}
                    type="submit"
                    variant="primary"
                  >
                    <MessageSquarePlus className="mr-2 h-4 w-4" strokeWidth={1.8} />
                    创建话题
                  </Button>
                </form>
                {error ? <p className="mt-3 text-left text-sm text-rose-700">{error}</p> : null}
              </Surface>
            </section>

            <section className="mx-auto mt-16 w-full max-w-3xl" aria-label="最近话题">
              <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">继续最近话题</h2>
                  <p className="mt-1 text-xs text-slate-500">从最近的工作上下文继续推进。</p>
                </div>
                {isLoading ? <p className="text-xs text-slate-400">正在加载...</p> : null}
              </div>

              {!isLoading && topics.length === 0 ? (
                <Surface className="rounded-[24px] border border-dashed border-slate-200 bg-white/70 p-8 text-center">
                  <p className="text-sm text-slate-500">当前还没有历史话题，从上方创建你的第一个话题。</p>
                </Surface>
              ) : null}

              <div className="grid gap-3">
                {topics.map((topic) => {
                  const deleting = deletingId === topic.id;
                  return (
                    <Surface
                      className="rounded-[24px] border border-white/70 bg-white/80 p-4 shadow-[0_10px_30px_rgba(15,23,42,0.05)]"
                      key={topic.id}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <Link
                          className="min-w-0 flex-1 rounded-2xl px-1 py-1 outline-none transition-opacity duration-200 hover:opacity-85"
                          to={`/topics/${topic.id}`}
                        >
                          <p className="truncate text-sm font-semibold text-slate-900">{topic.title}</p>
                          <p className="mt-1 line-clamp-1 text-sm text-slate-500">
                            {topic.description || "继续这个话题的当前工作。"}
                          </p>
                          <p className="mt-2 text-xs text-slate-400">{topic.updatedAt}</p>
                        </Link>

                        <div className="flex shrink-0 items-center gap-2">
                          <Link
                            aria-label={`进入${topic.title}`}
                            className="flex h-10 w-10 items-center justify-center rounded-2xl text-slate-500 transition-colors duration-200 hover:bg-slate-100 hover:text-slate-900"
                            to={`/topics/${topic.id}`}
                          >
                            <ArrowRight className="h-4 w-4" strokeWidth={1.8} />
                          </Link>
                          <button
                            aria-label={`删除${topic.title}`}
                            className="flex h-10 w-10 items-center justify-center rounded-2xl text-slate-400 transition-colors duration-200 hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-50"
                            disabled={deleting}
                            onClick={() => void handleDelete(topic.id)}
                            type="button"
                          >
                            <Trash2 className="h-4 w-4" strokeWidth={1.8} />
                          </button>
                        </div>
                      </div>
                    </Surface>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
