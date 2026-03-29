import { AnimatePresence, motion } from "framer-motion";
import { ArrowDown, ArrowUp, Check, ExternalLink, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { cn } from "../lib/cn";
import type { CandidatePost } from "../types/workspace";
import { Button } from "./ui/Button";

function buildInitialOrder(posts: CandidatePost[]): string[] {
  return posts
    .filter((post) => post.selected)
    .sort((left, right) => (left.manualOrder ?? Number.MAX_SAFE_INTEGER) - (right.manualOrder ?? Number.MAX_SAFE_INTEGER))
    .map((post) => post.id);
}

function sortPosts(posts: CandidatePost[], selectedOrder: string[]): CandidatePost[] {
  const orderIndexMap = new Map(selectedOrder.map((postId, index) => [postId, index]));

  return [...posts].sort((left, right) => {
    const leftSelected = orderIndexMap.has(left.id);
    const rightSelected = orderIndexMap.has(right.id);

    if (leftSelected && rightSelected) {
      return orderIndexMap.get(left.id)! - orderIndexMap.get(right.id)!;
    }

    if (leftSelected) {
      return -1;
    }

    if (rightSelected) {
      return 1;
    }

    return left.title.localeCompare(right.title, "zh-CN");
  });
}

function moveItem(order: string[], postId: string, direction: "up" | "down"): string[] {
  const index = order.indexOf(postId);

  if (index === -1) {
    return order;
  }

  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= order.length) {
    return order;
  }

  const next = [...order];
  [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
  return next;
}

export function CandidatePostsSection({ posts }: { posts: CandidatePost[] }): JSX.Element {
  const [selectedOrder, setSelectedOrder] = useState<string[]>(() => buildInitialOrder(posts));
  const [activePostId, setActivePostId] = useState<string | null>(null);
  const [activeImageIndex, setActiveImageIndex] = useState(0);

  useEffect(() => {
    setSelectedOrder(buildInitialOrder(posts));
  }, [posts]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        setActivePostId(null);
        return;
      }
      if (activePostId === null) {
        return;
      }
      if (event.key === "ArrowLeft") {
        setActiveImageIndex((current) => Math.max(0, current - 1));
      }
      if (event.key === "ArrowRight") {
        setActiveImageIndex((current) => {
          const active = posts.find((post) => post.id === activePostId);
          const total = active?.images.length ?? 0;
          return total > 0 ? Math.min(total - 1, current + 1) : current;
        });
      }
    }

    if (activePostId !== null) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [activePostId, posts]);

  const displayPosts = useMemo(() => sortPosts(posts, selectedOrder), [posts, selectedOrder]);
  const activePost = displayPosts.find((post) => post.id === activePostId) ?? null;
  const activeImages = activePost?.images ?? [];
  const currentImage = activeImages[activeImageIndex] ?? null;
  const hasMultipleImages = activeImages.length > 1;

  useEffect(() => {
    setActiveImageIndex(0);
  }, [activePostId]);

  function toggleSelected(postId: string): void {
    setSelectedOrder((current) => {
      if (current.includes(postId)) {
        return current.filter((value) => value !== postId);
      }

      return [...current, postId];
    });
  }

  function getOrder(postId: string): number | null {
    const index = selectedOrder.indexOf(postId);
    return index === -1 ? null : index + 1;
  }

  return (
    <>
      {displayPosts.length === 0 ? <p className="text-sm text-slate-500">空状态</p> : null}

      <div aria-label="搜索结果卡片流" className="flex flex-wrap items-start gap-2">
        {displayPosts.map((post) => {
          const order = getOrder(post.id);
          const selected = order !== null;

          return (
            <button
              aria-controls="candidate-post-detail-dialog"
              aria-expanded={activePostId === post.id}
              aria-haspopup="dialog"
              className={cn(
                "group relative w-[126px] shrink-0 overflow-hidden rounded-[16px] border bg-slate-50 text-left transition duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white",
                selected ? "border-blue-200 bg-blue-50/70" : "border-slate-200"
              )}
              key={post.id}
              onClick={() => {
                setActivePostId(post.id);
                setActiveImageIndex(0);
              }}
              type="button"
            >
              <img alt={`${post.title} 封面图`} className="aspect-[0.82] w-full object-cover" src={post.imageUrl} />
              <div className="px-2 py-1.5">
                <p className="truncate text-[11px] font-medium text-slate-700">{post.title}</p>
              </div>

              {selected ? (
                <span className="absolute right-1.5 top-1.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-semibold text-white">
                  {order}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <AnimatePresence>
        {activePost !== null ? (
          <motion.div
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/28 px-4"
            data-state="visible"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            onClick={() => setActivePostId(null)}
            role="presentation"
            transition={{ duration: 0.22, ease: "easeOut" }}
          >
            <motion.div
              animate={{ opacity: 1, scale: 1, y: 0 }}
              aria-labelledby="candidate-post-detail-title"
              aria-modal="true"
              className="w-full max-w-2xl rounded-[28px] border border-slate-200 bg-white p-5 shadow-floating"
              exit={{ opacity: 0, scale: 0.98, y: 10 }}
              id="candidate-post-detail-dialog"
              initial={{ opacity: 0, scale: 0.98, y: 12 }}
              onClick={(event) => event.stopPropagation()}
              role="dialog"
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400">帖子详情</p>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900" id="candidate-post-detail-title">
                    {activePost.title}
                  </h3>
                </div>
                <Button aria-label="关闭" onClick={() => setActivePostId(null)} size="icon" type="button" variant="ghost">
                  <X className="h-4 w-4" strokeWidth={1.8} />
                </Button>
              </div>

              <div className="mt-4 grid gap-5 md:grid-cols-[240px_minmax(0,1fr)]">
                <div>
                  <img
                    alt={currentImage?.alt ?? `${activePost.title} 详情图`}
                    className="w-full rounded-[22px] object-cover"
                    src={currentImage?.imageUrl ?? activePost.imageUrl}
                  />
                  {hasMultipleImages ? (
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <Button
                        aria-label="上一张图片"
                        disabled={activeImageIndex === 0}
                        onClick={() => setActiveImageIndex((current) => Math.max(0, current - 1))}
                        size="sm"
                        type="button"
                        variant="secondary"
                      >
                        上一张
                      </Button>
                      <div
                        aria-label="图片位置指示"
                        className="flex items-center gap-1.5"
                      >
                        {activeImages.map((image, index) => (
                          <button
                            aria-label={`切换到第 ${index + 1} 张图片`}
                            className={cn(
                              "h-2.5 w-2.5 rounded-full transition-colors duration-200",
                              index === activeImageIndex ? "bg-slate-900" : "bg-slate-300"
                            )}
                            key={image.id}
                            onClick={() => setActiveImageIndex(index)}
                            type="button"
                          />
                        ))}
                      </div>
                      <Button
                        aria-label="下一张图片"
                        disabled={activeImageIndex === activeImages.length - 1}
                        onClick={() =>
                          setActiveImageIndex((current) => Math.min(activeImages.length - 1, current + 1))
                        }
                        size="sm"
                        type="button"
                        variant="secondary"
                      >
                        下一张
                      </Button>
                    </div>
                  ) : null}
                </div>
                <div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span>作者：{activePost.author}</span>
                    <span>热度：{activePost.heat}</span>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-600">{activePost.bodyText}</p>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
                <a
                  className="inline-flex items-center gap-2 text-sm text-slate-500 transition-colors duration-200 hover:text-slate-900"
                  href={activePost.sourceUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  查看原帖
                  <ExternalLink className="h-4 w-4" strokeWidth={1.8} />
                </a>

                <div className="flex flex-wrap items-center gap-2">
                  {selectedOrder.includes(activePost.id) ? (
                    <>
                      <Button onClick={() => setSelectedOrder((current) => moveItem(current, activePost.id, "up"))} size="sm" type="button" variant="secondary">
                        <ArrowUp className="h-3.5 w-3.5" strokeWidth={1.8} />
                        上移
                      </Button>
                      <Button onClick={() => setSelectedOrder((current) => moveItem(current, activePost.id, "down"))} size="sm" type="button" variant="secondary">
                        <ArrowDown className="h-3.5 w-3.5" strokeWidth={1.8} />
                        下移
                      </Button>
                    </>
                  ) : null}

                  <Button onClick={() => toggleSelected(activePost.id)} type="button" variant="primary">
                    <Check className="h-4 w-4" strokeWidth={1.8} />
                    {selectedOrder.includes(activePost.id) ? "移出已选" : "加入已选"}
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
