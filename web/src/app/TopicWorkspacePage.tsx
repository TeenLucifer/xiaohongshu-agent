import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, SendHorizontal } from "lucide-react";
import { startTransition, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AgentTimeline } from "../components/AgentTimeline";
import { CandidatePostsSection } from "../components/CandidatePostsSection";
import { ContextPanelGroup } from "../components/ContextPanelGroup";
import { CopyDraftSummaryPanel } from "../components/CopyDraftSummaryPanel";
import { ImageResultsPanel } from "../components/ImageResultsPanel";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import {
  mockCandidatePostsByTopicId,
  mockChatMessagesByTopicId,
  mockCopyDraftByTopicId,
  mockImageTasksByTopicId,
  mockMaterialPreviewByTopicId,
  mockTopics,
  mockWorkspaces
} from "../data/mockTopics";
import type { ChatMessage, CopyDraftContent, WorkspaceSectionId } from "../types/workspace";

const defaultExpandedGroups: Record<WorkspaceSectionId, boolean> = {
  materials: false,
  collector: false,
  candidatePosts: true,
  patternSummary: false,
  copyDraft: false,
  imageResults: false,
  conversationTimeline: false
};

function createAgentReply(input: string): ChatMessage {
  return {
    id: `message-agent-${Date.now()}`,
    role: "agent",
    agentName: "协作 Agent",
    time: "刚刚",
    text: `我收到了这轮输入：“${input}”。当前前端原型会先把结果保留在聊天主栏里，后续接入真实后端和 agent 时再替换成实际返回。`
  };
}

export function TopicWorkspacePage(): JSX.Element {
  const { topicId: topicIdParam } = useParams<{ topicId: string }>();
  const topicId = topicIdParam ?? mockTopics[0].id;
  const workspace = mockWorkspaces[topicId];

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isContextOpen, setIsContextOpen] = useState(true);
  const [expandedGroups, setExpandedGroups] =
    useState<Record<WorkspaceSectionId, boolean>>(defaultExpandedGroups);
  const [composerValue, setComposerValue] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessagesByTopicId[topicId] ?? []);
  const [copyDraft, setCopyDraft] = useState<CopyDraftContent | undefined>(mockCopyDraftByTopicId[topicId]);

  useEffect(() => {
    setExpandedGroups(defaultExpandedGroups);
    setComposerValue("");
    setMessages(mockChatMessagesByTopicId[topicId] ?? []);
    setCopyDraft(mockCopyDraftByTopicId[topicId]);
    setIsSidebarCollapsed(false);
  }, [topicId]);

  const sectionsById = useMemo(() => {
    if (workspace === undefined) {
      return {};
    }

    return Object.fromEntries(workspace.sections.map((section) => [section.id, section]));
  }, [workspace]);

  function toggleGroup(sectionId: WorkspaceSectionId): void {
    setExpandedGroups((current) => ({ ...current, [sectionId]: !current[sectionId] }));
  }

  function handleSend(): void {
    const value = composerValue.trim();
    if (value.length === 0) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `message-user-${Date.now()}`,
      role: "user",
      text: value,
      time: "刚刚"
    };

    startTransition(() => {
      setMessages((current) => [...current, userMessage, createAgentReply(value)]);
      setComposerValue("");
    });
  }

  if (workspace === undefined) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <Surface className="max-w-lg p-8 text-center">
          <h1 className="text-2xl font-semibold text-slate-900">未找到话题</h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">请从左侧切换到一个有效话题继续查看工作台。</p>
        </Surface>
      </main>
    );
  }

  const materials = mockMaterialPreviewByTopicId[topicId] ?? [];
  const candidatePosts = mockCandidatePostsByTopicId[topicId] ?? [];
  const imageGroups = mockImageTasksByTopicId[topicId] ?? [];

  return (
    <motion.main
      animate={{
        gridTemplateColumns:
          isSidebarCollapsed && isContextOpen
            ? "80px minmax(520px, 560px) minmax(640px, 1fr)"
            : isSidebarCollapsed && !isContextOpen
              ? "80px minmax(520px, 560px) 88px"
              : !isSidebarCollapsed && isContextOpen
                ? "248px minmax(520px, 560px) minmax(560px, 1fr)"
                : "248px minmax(520px, 560px) 88px"
      }}
      className="grid h-screen gap-4 pr-4 pl-0"
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
      />

      <section
        aria-label="Agent 对话主栏"
        className="my-4 flex h-[calc(100vh-2rem)] min-w-0 self-center flex-col overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 px-6 py-6 shadow-surface"
        data-testid="workspace-main-column"
      >
        <div className="mx-auto flex w-full max-w-[720px] items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Topic Workspace</p>
            <h1 className="mt-3 text-[31px] font-semibold tracking-[-0.03em] text-slate-950">{workspace.topic.title}</h1>
            <p className="mt-2 max-w-2xl text-[13px] leading-6 text-slate-500">{workspace.topic.description}</p>
          </div>
          <Badge variant="primary">{sectionsById.collector?.status === "loading" ? "搜集中" : "已就绪"}</Badge>
        </div>

        <div className="scrollbar-subtle mt-6 flex-1 overflow-y-auto pr-2">
          <div className="mx-auto w-full max-w-[720px]">
            <AgentTimeline copyDraft={copyDraft} messages={messages} onCopyDraftChange={setCopyDraft} />
          </div>
        </div>

        <div className="mx-auto mt-5 w-full max-w-[720px]">
          <div className="flex items-center gap-3 rounded-[24px] border border-slate-200 bg-slate-50 px-3 py-3 shadow-sm">
            <input
              aria-label="对话输入框"
              className="h-11 flex-1 border-0 bg-transparent px-2 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              onChange={(event) => setComposerValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="输入你想继续让 Agent 处理的内容..."
              type="text"
              value={composerValue}
            />
            <Button aria-label="发送消息" onClick={handleSend} size="icon" type="button" variant="primary">
              <SendHorizontal className="h-4 w-4" strokeWidth={1.8} />
            </Button>
          </div>
        </div>
      </section>

      <motion.aside
        aria-label="当前工作区"
        className="my-4 h-[calc(100vh-2rem)] self-center overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 shadow-surface"
        data-state={isContextOpen ? "open" : "collapsed"}
        data-testid="workspace-context-column"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4">
            {isContextOpen ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Current Workspace</p>
                <h2 className="mt-2 text-lg font-semibold text-slate-900">当前工作区</h2>
              </div>
            ) : (
              <div className="mx-auto" />
            )}

            <Button
              aria-label={isContextOpen ? "收起工作区" : "展开工作区"}
              onClick={() => setIsContextOpen((current) => !current)}
              size="icon"
              type="button"
              variant="ghost"
            >
              {isContextOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
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
                            {material.type === "image" ? "图片" : material.type === "text" ? "文本" : "链接"}
                          </p>
                          <p className="mt-2 text-sm font-medium text-slate-900">{material.label}</p>
                          <p className="mt-1 text-xs leading-5 text-slate-500">{material.detail}</p>
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

              {sectionsById.copyDraft ? (
                <ContextPanelGroup
                  expanded={expandedGroups.copyDraft}
                  onToggle={() => toggleGroup("copyDraft")}
                  section={sectionsById.copyDraft}
                >
                  {copyDraft ? <CopyDraftSummaryPanel copyDraft={copyDraft} /> : <p className="text-sm text-slate-500">空状态</p>}
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
            <div className="flex flex-1 items-start justify-center pt-4">
              <div className="writing-mode-vertical text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-300 [writing-mode:vertical-rl]">
                Workspace
              </div>
            </div>
          )}
        </div>
      </motion.aside>
    </motion.main>
  );
}
