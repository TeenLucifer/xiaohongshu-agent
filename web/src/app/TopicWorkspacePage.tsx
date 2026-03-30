import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, SendHorizontal, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AgentTimeline } from "../components/AgentTimeline";
import { CandidatePostsSection } from "../components/CandidatePostsSection";
import { ContextPanelGroup } from "../components/ContextPanelGroup";
import { CopyDraftSummaryPanel } from "../components/CopyDraftSummaryPanel";
import { ImageResultsPanel } from "../components/ImageResultsPanel";
import { PatternSummarySection } from "../components/PatternSummarySection";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import {
  deleteTopic,
  getWorkspace,
  getWorkspaceContext,
  listTopics,
  runTopic,
  toChatMessages,
  toTopicCards,
} from "../lib/api";
import {
  mockChatMessagesByTopicId,
  mockCopyDraftByTopicId,
  mockImageTasksByTopicId,
  mockMaterialPreviewByTopicId,
} from "../data/mockTopics";
import type {
  CandidatePost,
  ChatMessage,
  CopyDraftContent,
  PatternSummaryContent,
  TopicCard,
  WorkspaceSection,
  WorkspaceSectionId,
} from "../types/workspace";

const defaultExpandedGroups: Record<WorkspaceSectionId, boolean> = {
  materials: false,
  collector: false,
  candidatePosts: true,
  patternSummary: false,
  copyDraft: false,
  imageResults: false,
  conversationTimeline: false,
};

const defaultWorkspaceSections: WorkspaceSection[] = [
  { id: "materials", title: "素材", status: "empty", summary: "当前还没有上传素材。" },
  { id: "collector", title: "搜集", status: "empty", summary: "等待开始搜集。" },
  { id: "candidatePosts", title: "搜索结果", status: "empty", summary: "还没有候选帖子。" },
  { id: "patternSummary", title: "总结", status: "empty", summary: "还没有总结结果。" },
  { id: "copyDraft", title: "文案", status: "empty", summary: "还没有文案草稿。" },
  { id: "imageResults", title: "图片", status: "empty", summary: "还没有图片结果。" },
  { id: "conversationTimeline", title: "对话", status: "empty", summary: "还没有会话记录。" },
];

function buildWorkspaceSections({
  candidatePosts,
  copyDraft,
  hasMessages,
  imageGroupCount,
  isSending,
  patternSummary,
}: {
  candidatePosts: CandidatePost[];
  copyDraft: CopyDraftContent | undefined;
  hasMessages: boolean;
  imageGroupCount: number;
  isSending: boolean;
  patternSummary: PatternSummaryContent | undefined;
}): WorkspaceSection[] {
  const candidateCount = candidatePosts.length;
  return [
    { id: "materials", title: "素材", status: "empty", summary: "当前还没有上传素材。" },
    {
      id: "collector",
      title: "搜集",
      status: isSending ? "loading" : candidateCount > 0 ? "success" : "empty",
      summary:
        candidateCount > 0
          ? `当前已整理 ${candidateCount} 条候选帖子。`
          : "等待开始搜集。",
    },
    {
      id: "candidatePosts",
      title: "搜索结果",
      status: candidateCount > 0 ? "success" : "empty",
      summary:
        candidateCount > 0
          ? `已返回 ${candidateCount} 条候选帖子，支持查看详情。`
          : "还没有候选帖子。",
    },
    {
      id: "patternSummary",
      title: "总结",
      status: patternSummary ? "success" : "empty",
      summary: patternSummary ? "当前总结结果已同步到工作区。" : "还没有总结结果。",
    },
    {
      id: "copyDraft",
      title: "文案",
      status: copyDraft ? "success" : "empty",
      summary: copyDraft ? "当前文案支持在中栏进入编辑态。" : "还没有文案草稿。",
    },
    {
      id: "imageResults",
      title: "图片",
      status: imageGroupCount > 0 ? "success" : "empty",
      summary: imageGroupCount > 0 ? "当前图片结果已准备就绪。" : "还没有图片结果。",
    },
    {
      id: "conversationTimeline",
      title: "对话",
      status: hasMessages ? "success" : "empty",
      summary: hasMessages ? "主栏仅展示 user / agent 对话。" : "还没有会话记录。",
    },
  ];
}

export function TopicWorkspacePage(): JSX.Element {
  const navigate = useNavigate();
  const { topicId: topicIdParam } = useParams<{ topicId: string }>();
  const [topics, setTopics] = useState<TopicCard[]>([]);
  const [isTopicsLoading, setIsTopicsLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isContextOpen, setIsContextOpen] = useState(true);
  const [expandedGroups, setExpandedGroups] =
    useState<Record<WorkspaceSectionId, boolean>>(defaultExpandedGroups);
  const [composerValue, setComposerValue] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [copyDraft, setCopyDraft] = useState<CopyDraftContent | undefined>();
  const [candidatePosts, setCandidatePosts] = useState<CandidatePost[]>([]);
  const [patternSummary, setPatternSummary] = useState<PatternSummaryContent | undefined>();
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isDeletingTopic, setIsDeletingTopic] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsTopicsLoading(true);
    void listTopics()
      .then((response) => {
        if (!cancelled) {
          const topicCards = toTopicCards(response.items);
          setTopics(topicCards.length > 0 ? topicCards : []);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTopics([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsTopicsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const topicId = topicIdParam ?? topics[0]?.id ?? "";
  const topic = topics.find((item) => item.id === topicId);

  useEffect(() => {
    setExpandedGroups(defaultExpandedGroups);
    setComposerValue("");
    setMessages([]);
    setCopyDraft(mockCopyDraftByTopicId[topicId]);
    // candidatePosts / patternSummary 已接真实后端，不再先注入 mock，避免切换 topic 时闪现旧假数据。
    setCandidatePosts([]);
    setPatternSummary(undefined);
    setIsSidebarCollapsed(false);
  }, [topicId]);

  useEffect(() => {
    if (topic === undefined) {
      return;
    }

    let cancelled = false;
    setIsMessagesLoading(true);
    setMessagesError(null);
    void getWorkspace(topicId, topic.title)
      .then((response) => {
        if (!cancelled) {
          setMessages(toChatMessages(response.messages));
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "加载会话失败";
          setMessagesError(message);
          setMessages(mockChatMessagesByTopicId[topicId] ?? []);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsMessagesLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [topicId, topic]);

  useEffect(() => {
    if (topic === undefined) {
      return;
    }

    let cancelled = false;
    void getWorkspaceContext(topicId, topic.title)
      .then((response) => {
        if (!cancelled) {
          setCandidatePosts(response.candidate_posts);
          setPatternSummary(response.pattern_summary ?? undefined);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCandidatePosts([]);
          setPatternSummary(undefined);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [topicId, topic]);

  const workspaceSections = useMemo(
    () =>
      buildWorkspaceSections({
        candidatePosts,
        copyDraft,
        hasMessages: messages.length > 0,
        imageGroupCount: (mockImageTasksByTopicId[topicId] ?? []).length,
        isSending,
        patternSummary,
      }),
    [candidatePosts, copyDraft, isSending, messages.length, patternSummary, topicId]
  );

  const sectionsById = useMemo(() => {
    if (topic === undefined) {
      return {};
    }
    return Object.fromEntries(workspaceSections.map((section) => [section.id, section]));
  }, [topic, workspaceSections]);

  function toggleGroup(sectionId: WorkspaceSectionId): void {
    setExpandedGroups((current) => ({ ...current, [sectionId]: !current[sectionId] }));
  }

  const shellColumns =
    isSidebarCollapsed && isContextOpen
      ? "80px minmax(520px, 560px) minmax(640px, 1fr)"
      : isSidebarCollapsed && !isContextOpen
        ? "80px minmax(520px, 1fr) 72px"
        : !isSidebarCollapsed && isContextOpen
          ? "248px minmax(520px, 560px) minmax(560px, 1fr)"
          : "248px minmax(520px, 1fr) 72px";

  async function handleSend(): Promise<void> {
    const value = composerValue.trim();
    if (value.length === 0 || topic === undefined || isSending) {
      return;
    }
    setIsSending(true);
    setMessagesError(null);
    try {
      const response = await runTopic(topicId, topic.title, value);
      setMessages(toChatMessages(response.messages));
      setComposerValue("");
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "发送失败";
      setMessagesError(message);
    } finally {
      setIsSending(false);
    }
  }

  async function handleDeleteCurrentTopic(): Promise<void> {
    if (topic === undefined || isDeletingTopic) {
      return;
    }
    setIsDeletingTopic(true);
    setMessagesError(null);
    try {
      await deleteTopic(topicId);
      const response = await listTopics();
      const remaining = toTopicCards(response.items);
      setTopics(remaining);
      if (remaining.length > 0) {
        navigate(`/topics/${remaining[0].id}`);
      } else {
        navigate("/");
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "删除话题失败";
      setMessagesError(message);
    } finally {
      setIsDeletingTopic(false);
    }
  }

  if (topic === undefined) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <Surface className="max-w-lg p-8 text-center">
          <h1 className="text-2xl font-semibold text-slate-900">
            {isTopicsLoading ? "正在加载话题" : "未找到话题"}
          </h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">
            {isTopicsLoading ? "正在从后端读取 topic 列表..." : "请先返回话题列表，或创建一个新的话题。"}
          </p>
          <div className="mt-6">
            <Button onClick={() => navigate("/")} type="button" variant="primary">
              返回话题列表
            </Button>
          </div>
        </Surface>
      </main>
    );
  }

  const materials = mockMaterialPreviewByTopicId[topicId] ?? [];
  const imageGroups = mockImageTasksByTopicId[topicId] ?? [];

  return (
    <motion.main
      animate={{ gridTemplateColumns: shellColumns }}
      className="grid h-screen gap-4 pr-4 pl-0"
      style={{ width: "100%" }}
      data-grid-columns={shellColumns}
      data-left-sidebar={isSidebarCollapsed ? "collapsed" : "open"}
      data-right-context={isContextOpen ? "open" : "collapsed"}
      data-state={isContextOpen ? "open" : "collapsed"}
      data-testid="workspace-shell"
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <WorkspaceSidebar
        collapsed={isSidebarCollapsed}
        currentTopicId={topicId}
        onToggleCollapse={() => setIsSidebarCollapsed((current) => !current)}
        topics={topics}
      />

      <section
        aria-label="Agent 对话主栏"
        className="my-4 flex h-[calc(100vh-2rem)] min-w-0 self-center flex-col overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 px-6 py-6 shadow-surface"
        data-testid="workspace-main-column"
      >
        <div className="mx-auto flex w-full max-w-[720px] items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Topic Workspace
            </p>
            <h1 className="mt-3 text-[31px] font-semibold tracking-[-0.03em] text-slate-950">
              {topic.title}
            </h1>
            <p className="mt-2 max-w-2xl text-[13px] leading-6 text-slate-500">
              {topic.description || "当前话题还没有描述。"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="primary">
              {sectionsById.collector?.status === "loading" ? "搜集中" : "已就绪"}
            </Badge>
            <Button
              aria-label="删除当前话题"
              disabled={isDeletingTopic}
              onClick={() => void handleDeleteCurrentTopic()}
              type="button"
              variant="ghost"
            >
              <Trash2 className="h-4 w-4" strokeWidth={1.8} />
            </Button>
          </div>
        </div>

        <div className="scrollbar-subtle mt-6 flex-1 overflow-y-auto pr-2">
          <div className="mx-auto w-full max-w-[720px]">
            {messagesError ? (
              <Surface className="mb-4 border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700">
                {messagesError}
              </Surface>
            ) : null}
            {isMessagesLoading && messages.length === 0 ? (
              <Surface className="mb-4 p-4 text-sm text-slate-500">正在加载会话...</Surface>
            ) : null}
            <AgentTimeline copyDraft={copyDraft} messages={messages} onCopyDraftChange={setCopyDraft} />
          </div>
        </div>

        <div className="mx-auto mt-5 w-full max-w-[720px]">
          <div className="flex items-center gap-3 rounded-[24px] border border-slate-200 bg-slate-50 px-3 py-3 shadow-sm">
            <input
              aria-label="对话输入框"
              className="h-11 flex-1 border-0 bg-transparent px-2 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              disabled={isSending}
              onChange={(event) => setComposerValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="输入你想继续让 Agent 处理的内容..."
              type="text"
              value={composerValue}
            />
            <Button
              aria-label="发送消息"
              disabled={isSending}
              onClick={() => void handleSend()}
              size="icon"
              type="button"
              variant="primary"
            >
              <SendHorizontal className="h-4 w-4" strokeWidth={1.8} />
            </Button>
          </div>
        </div>
      </section>

      <motion.aside
        aria-label="右侧面板"
        className="my-4 h-[calc(100vh-2rem)] self-center overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 shadow-surface"
        data-collapse-direction="right"
        data-state={isContextOpen ? "open" : "collapsed"}
        data-testid="workspace-context-column"
      >
        <div className="flex h-full flex-col">
          <div
            className={
              isContextOpen
                ? "flex items-center justify-between border-b border-slate-100 px-4 py-4"
                : "flex items-start justify-end px-3 py-3"
            }
          >
            {isContextOpen ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Context Panels
                </p>
                <h2 className="mt-2 text-lg font-semibold text-slate-900">内容面板</h2>
              </div>
            ) : (
              <div />
            )}

            <Button
              aria-label={isContextOpen ? "收起工作区" : "展开工作区"}
              onClick={() => setIsContextOpen((current) => !current)}
              size="icon"
              type="button"
              variant="ghost"
            >
              {isContextOpen ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>

          {isContextOpen ? (
            <div className="scrollbar-subtle flex-1 space-y-3 overflow-y-auto px-3 py-3">
              {sectionsById.materials ? (
                <ContextPanelGroup
                  expanded={expandedGroups.materials}
                  onToggle={() => toggleGroup("materials")}
                  section={sectionsById.materials}
                >
                  {materials.length === 0 ? (
                    <p className="text-sm text-slate-500">空状态</p>
                  ) : (
                    <div className="grid gap-2">
                      {materials.map((material) => (
                        <article className="rounded-[18px] bg-slate-50 p-3" key={material.id}>
                          <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">
                            {material.type === "image"
                              ? "图片"
                              : material.type === "text"
                                ? "文本"
                                : "链接"}
                          </p>
                          <p className="mt-2 text-sm font-medium text-slate-900">
                            {material.label}
                          </p>
                          <p className="mt-1 text-xs leading-5 text-slate-500">
                            {material.detail}
                          </p>
                        </article>
                      ))}
                    </div>
                  )}
                </ContextPanelGroup>
              ) : null}

              {sectionsById.candidatePosts ? (
                <ContextPanelGroup
                  expanded={expandedGroups.candidatePosts}
                  onToggle={() => toggleGroup("candidatePosts")}
                  section={sectionsById.candidatePosts}
                >
                  <CandidatePostsSection posts={candidatePosts} />
                </ContextPanelGroup>
              ) : null}

              {sectionsById.patternSummary ? (
                <ContextPanelGroup
                  expanded={expandedGroups.patternSummary}
                  onToggle={() => toggleGroup("patternSummary")}
                  section={sectionsById.patternSummary}
                >
                  {patternSummary ? (
                    <PatternSummarySection
                      content={patternSummary}
                      section={sectionsById.patternSummary}
                    />
                  ) : (
                    <p className="text-sm text-slate-500">空状态</p>
                  )}
                </ContextPanelGroup>
              ) : null}

              {sectionsById.copyDraft ? (
                <ContextPanelGroup
                  expanded={expandedGroups.copyDraft}
                  onToggle={() => toggleGroup("copyDraft")}
                  section={sectionsById.copyDraft}
                >
                  {copyDraft ? (
                    <CopyDraftSummaryPanel copyDraft={copyDraft} />
                  ) : (
                    <p className="text-sm text-slate-500">空状态</p>
                  )}
                </ContextPanelGroup>
              ) : null}

              {sectionsById.imageResults ? (
                <ContextPanelGroup
                  expanded={expandedGroups.imageResults}
                  onToggle={() => toggleGroup("imageResults")}
                  section={sectionsById.imageResults}
                >
                  <ImageResultsPanel groups={imageGroups} />
                </ContextPanelGroup>
              ) : null}
            </div>
          ) : (
            <div className="flex flex-1 items-start justify-end px-3" />
          )}
        </div>
      </motion.aside>
    </motion.main>
  );
}
