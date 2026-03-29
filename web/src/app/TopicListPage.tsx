import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import { createTopic, deleteTopic, listTopics, toTopicCards } from "../lib/api";
import type { TopicCard } from "../types/workspace";

export function TopicListPage(): JSX.Element {
  const navigate = useNavigate();
  const [topics, setTopics] = useState<TopicCard[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
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
      const created = await createTopic(topicTitle, description.trim());
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
    <main className="page-shell">
      <header className="page-header">
        <p className="eyebrow">Frontend Feature 023</p>
        <h1>话题列表</h1>
        <p className="page-description">通过真实 topic API 管理话题入口，并跳转到对应工作台。</p>
      </header>

      <Surface className="mb-6 p-5">
        <div className="grid gap-3">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-900" htmlFor="topic-title">
              话题标题
            </label>
            <input
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
              id="topic-title"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="输入新的话题标题"
              type="text"
              value={title}
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-900" htmlFor="topic-description">
              话题描述
            </label>
            <textarea
              className="min-h-24 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
              id="topic-description"
              onChange={(event) => setDescription(event.target.value)}
              placeholder="可选，补充这个话题的目标和范围"
              value={description}
            />
          </div>
          <div className="flex items-center gap-3">
            <Button disabled={isSubmitting} onClick={() => void handleCreate()} type="button" variant="primary">
              创建话题
            </Button>
            {error ? <p className="text-sm text-rose-700">{error}</p> : null}
          </div>
        </div>
      </Surface>

      {isLoading ? <p className="mb-4 text-sm text-slate-500">正在加载话题列表...</p> : null}

      <section className="topic-grid" aria-label="话题列表">
        {topics.map((topic) => {
          const deleting = deletingId === topic.id;
          return (
            <article className="topic-card" key={topic.id}>
              <Link className="block" to={`/topics/${topic.id}`}>
                <div className="topic-card-meta">
                  <span>最近更新</span>
                  <strong>{topic.updatedAt}</strong>
                </div>
                <h2>{topic.title}</h2>
                <p>{topic.description || "暂无描述"}</p>
              </Link>
              <div className="mt-4 flex items-center justify-between gap-3">
                <Link className="topic-card-action" to={`/topics/${topic.id}`}>
                  进入工作台
                </Link>
                <Button
                  disabled={deleting}
                  onClick={() => void handleDelete(topic.id)}
                  type="button"
                  variant="ghost"
                >
                  删除话题
                </Button>
              </div>
            </article>
          );
        })}
      </section>

      {!isLoading && topics.length === 0 ? (
        <Surface className="mt-6 p-6 text-center text-sm text-slate-500">当前还没有话题，请先创建一个。</Surface>
      ) : null}
    </main>
  );
}
