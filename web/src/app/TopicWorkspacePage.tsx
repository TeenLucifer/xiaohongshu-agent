import { motion } from "framer-motion";
import { ChevronDown, SendHorizontal, Trash2 } from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AgentTimeline } from "../components/AgentTimeline";
import { CandidatePostsSection } from "../components/CandidatePostsSection";
import { ContextPanelGroup } from "../components/ContextPanelGroup";
import { CopyDraftSummaryPanel } from "../components/CopyDraftSummaryPanel";
import { ImageEditorSection } from "../components/ImageEditorSection";
import { ImageResultsPanel } from "../components/ImageResultsPanel";
import { PatternSummarySection } from "../components/PatternSummarySection";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import {
  deleteMaterial,
  deleteCandidatePost,
  deleteImageResult,
  deleteTopic,
  getWorkspace,
  getWorkspaceContext,
  getMessages,
  listTopics,
  polishCopyDraftSelection,
  runTopic,
  streamTopicRun,
  toChatMessages,
  toTopicCards,
  uploadImageMaterials,
  updateEditorImages,
  updateCopyDraft,
} from "../lib/api";
import { mockChatMessagesByTopicId } from "../data/mockTopics";
import type {
  CandidatePost,
  ChatMessage,
  CopyDraftContent,
  EditorImage,
  GeneratedImageResult,
  MaterialItem,
  MaterialImage,
  PatternSummaryContent,
  ToolSummaryItem,
  TopicCard,
  WorkspaceSection,
  WorkspaceSectionId,
} from "../types/workspace";

const defaultExpandedGroups: Record<WorkspaceSectionId, boolean> = {
  collector: false,
  candidatePosts: true,
  patternSummary: false,
  copyDraft: false,
  imageResults: false,
  conversationTimeline: false,
};

const GENERATE_PATTERN_SUMMARY_PROMPT =
  "请基于当前保留帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。";

const GENERATE_COPY_DRAFT_PROMPT =
  "请基于当前保留帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。";

function InlineRunComposer({
  ariaLabel,
  busyText,
  buttonLabel = "发送",
  disabled,
  onChange,
  onSubmit,
  placeholder,
  value,
}: {
  ariaLabel: string;
  busyText?: string;
  buttonLabel?: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder: string;
  value: string;
}): JSX.Element {
  const displayedValue = busyText ?? value;
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    const element = textareaRef.current;
    if (element === null) {
      return;
    }
    element.style.height = "0px";
    const nextHeight = Math.min(Math.max(element.scrollHeight, 44), 144);
    element.style.height = `${nextHeight}px`;
  }, [displayedValue]);

  return (
    <div className="flex items-end gap-2 rounded-[18px] border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <textarea
        aria-label={ariaLabel}
        aria-busy={disabled ? "true" : "false"}
        className="max-h-36 min-h-[44px] flex-1 resize-none overflow-y-auto border-0 bg-transparent px-1 py-[10px] text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400"
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
          }
        }}
        placeholder={placeholder}
        ref={textareaRef}
        rows={1}
        value={displayedValue}
      />
      <Button
        aria-label={buttonLabel}
        disabled={disabled}
        onClick={onSubmit}
        size="icon"
        type="button"
        variant="ghost"
      >
        <SendHorizontal className="h-4 w-4" strokeWidth={1.8} />
      </Button>
    </div>
  );
}

function buildWorkspaceSections({
  candidatePosts,
  copyDraft,
  hasMessages,
  imageResultCount,
  isSending,
  patternSummary,
}: {
  candidatePosts: CandidatePost[];
  copyDraft: CopyDraftContent | undefined;
  hasMessages: boolean;
  imageResultCount: number;
  isSending: boolean;
  patternSummary: PatternSummaryContent | undefined;
}): WorkspaceSection[] {
  const candidateCount = candidatePosts.length;
  return [
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
      summary: copyDraft ? "当前文案可在右侧继续编辑。" : "还没有文案草稿。",
    },
    {
      id: "imageResults",
      title: "图片",
      status: imageResultCount > 0 ? "success" : "empty",
      summary: imageResultCount > 0 ? `当前已生成 ${imageResultCount} 张图片。` : "还没有图片结果。",
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
  const [expandedGroups, setExpandedGroups] =
    useState<Record<WorkspaceSectionId, boolean>>(defaultExpandedGroups);
  const [composerValue, setComposerValue] = useState("");
  const [candidateComposerValue, setCandidateComposerValue] = useState("");
  const [imageComposerValue, setImageComposerValue] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [copyDraft, setCopyDraft] = useState<CopyDraftContent | undefined>();
  const [candidatePosts, setCandidatePosts] = useState<CandidatePost[]>([]);
  const [patternSummary, setPatternSummary] = useState<PatternSummaryContent | undefined>();
  const [editorImages, setEditorImages] = useState<EditorImage[]>([]);
  const [imageResults, setImageResults] = useState<GeneratedImageResult[]>([]);
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sendingOrigin, setSendingOrigin] = useState<"conversation" | "candidate" | "image" | null>(
    null
  );
  const [isDeletingTopic, setIsDeletingTopic] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [activeContextTab, setActiveContextTab] = useState<"创作" | "对话">("创作");
  const timelineScrollRef = useRef<HTMLDivElement | null>(null);
  const copyDraftSaveTimerRef = useRef<number | null>(null);
  const conversationComposerRef = useRef<HTMLTextAreaElement | null>(null);
  const [isCopyDraftSaving, setIsCopyDraftSaving] = useState(false);

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

  async function loadWorkspaceContext(nextTopicId: string, nextTopicTitle: string): Promise<void> {
    const response = await getWorkspaceContext(nextTopicId, nextTopicTitle);
    setMaterials(response.materials ?? []);
    setCandidatePosts(response.candidate_posts);
    setPatternSummary(response.pattern_summary ?? undefined);
    setCopyDraft(response.copy_draft ?? undefined);
    setEditorImages(response.editor_images ?? []);
    setImageResults(response.image_results ?? []);
  }

  useEffect(() => {
    setExpandedGroups(defaultExpandedGroups);
    setComposerValue("");
    setCandidateComposerValue("");
    setImageComposerValue("");
    setMessages([]);
    setMaterials([]);
    setCopyDraft(undefined);
    // candidatePosts / patternSummary 已接真实后端，不再先注入 mock，避免切换 topic 时闪现旧假数据。
    setCandidatePosts([]);
    setPatternSummary(undefined);
    setEditorImages([]);
    setImageResults([]);
    setIsSidebarCollapsed(false);
    setActiveContextTab("创作");
    setIsCopyDraftSaving(false);
    if (copyDraftSaveTimerRef.current !== null) {
      window.clearTimeout(copyDraftSaveTimerRef.current);
      copyDraftSaveTimerRef.current = null;
    }
  }, [topicId]);

  useEffect(() => {
    return () => {
      if (copyDraftSaveTimerRef.current !== null) {
        window.clearTimeout(copyDraftSaveTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const container = timelineScrollRef.current;
    if (container === null) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      const targetTop = container.scrollHeight;
      container.scrollTop = targetTop;
      if (typeof container.scrollTo === "function") {
        container.scrollTo({ top: targetTop, behavior: "smooth" });
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, [messages]);

  useLayoutEffect(() => {
    const element = conversationComposerRef.current;
    if (element === null) {
      return;
    }
    element.style.height = "0px";
    const nextHeight = Math.min(Math.max(element.scrollHeight, 44), 176);
    element.style.height = `${nextHeight}px`;
  }, [composerValue]);

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
    void loadWorkspaceContext(topicId, topic.title)
      .then(() => {
        if (cancelled) {
          return;
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMaterials([]);
          setCandidatePosts([]);
          setPatternSummary(undefined);
          setCopyDraft(undefined);
          setEditorImages([]);
          setImageResults([]);
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
        imageResultCount: imageResults.length,
        isSending,
        patternSummary,
      }),
    [candidatePosts, copyDraft, imageResults.length, isSending, messages.length, patternSummary]
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

  const shellColumns = isSidebarCollapsed ? "80px minmax(0, 1fr)" : "248px minmax(0, 1fr)";

  function appendStreamingToolSummary(
    items: ToolSummaryItem[],
    nextItem: ToolSummaryItem
  ): ToolSummaryItem[] {
    const existingIndex = items.findIndex((item) => item.id === nextItem.id);
    if (existingIndex === -1) {
      return [...items, nextItem];
    }
    return items.map((item, index) => (index === existingIndex ? { ...item, ...nextItem } : item));
  }

  function updateStreamingAgentMessage(
    messageId: string,
    updater: (current: ChatMessage) => ChatMessage
  ): void {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId && message.role === "agent" ? updater(message) : message
      )
    );
  }

  async function handleSendMessage(
    rawValue: string,
    origin: "conversation" | "candidate" | "image" = "conversation"
  ): Promise<void> {
    const value = rawValue.trim();
    if (value.length === 0 || topic === undefined || isSending) {
      return;
    }
    const previousMessages = messages;
    const timestampLabel = "刚刚";
    const userMessageId = `user-stream:${Date.now()}`;
    const agentMessageId = `agent-stream:${Date.now()}`;
    setIsSending(true);
    setSendingOrigin(origin);
    setMessagesError(null);
    if (origin === "conversation") {
      setComposerValue("");
    }
    setMessages((current) => [
      ...current,
      {
        id: userMessageId,
        role: "user",
        text: value,
        time: timestampLabel,
      },
      {
        id: agentMessageId,
        role: "agent",
        text: "",
        time: timestampLabel,
        agentName: "协作 Agent",
        toolSummary: [],
        status: "streaming",
      },
    ]);
    try {
      await streamTopicRun(topicId, topic.title, value, (event) => {
        if (event.type === "tool_call_started") {
          updateStreamingAgentMessage(agentMessageId, (message) => ({
            ...message,
            toolSummary: appendStreamingToolSummary(message.toolSummary ?? [], {
              id: String(event.payload.tool_call_id ?? `${Date.now()}`),
              name: String(event.payload.name ?? "unknown_tool"),
              argumentsSummary: String(event.payload.arguments_summary ?? "{}"),
              resultSummary: "运行中...",
            }),
          }));
          return;
        }
        if (event.type === "tool_call_finished") {
          updateStreamingAgentMessage(agentMessageId, (message) => ({
            ...message,
            toolSummary: appendStreamingToolSummary(message.toolSummary ?? [], {
              id: String(event.payload.tool_call_id ?? `${Date.now()}`),
              name: String(event.payload.name ?? "unknown_tool"),
              argumentsSummary: String(event.payload.arguments_summary ?? "{}"),
              resultSummary: String(event.payload.result_summary ?? ""),
            }),
          }));
          return;
        }
        if (event.type === "assistant_delta") {
          updateStreamingAgentMessage(agentMessageId, (message) => ({
            ...message,
            text: message.text + String(event.payload.delta ?? ""),
          }));
          return;
        }
        if (event.type === "run_completed") {
          updateStreamingAgentMessage(agentMessageId, (message) => ({
            ...message,
            text: String(event.payload.final_text ?? message.text),
            toolSummary:
              Array.isArray(event.payload.tool_calls)
                ? (event.payload.tool_calls as Array<{
                    name?: string;
                    arguments_summary?: string;
                    result_summary?: string;
                  }>).map((item, index) => ({
                    id: `${message.id}:tool:${index}`,
                    name: item.name ?? "unknown_tool",
                    argumentsSummary: item.arguments_summary ?? "{}",
                    resultSummary: item.result_summary ?? "",
                  }))
                : message.toolSummary,
            status: "completed",
          }));
          return;
        }
        if (event.type === "run_failed") {
          updateStreamingAgentMessage(agentMessageId, (message) => ({
            ...message,
            text: String(event.payload.message ?? "运行失败"),
            status: "failed",
          }));
          setMessagesError(String(event.payload.message ?? "运行失败"));
        }
      });
      const latestMessages = await getMessages(topicId, topic.title);
      setMessages(toChatMessages(latestMessages.messages));
      await loadWorkspaceContext(topicId, topic.title);
    } catch (error: unknown) {
      setMessages(previousMessages);
      try {
        const response = await runTopic(topicId, topic.title, value);
        setMessages(toChatMessages(response.messages));
        await loadWorkspaceContext(topicId, topic.title);
      } catch (fallbackError: unknown) {
        const message = fallbackError instanceof Error ? fallbackError.message : "发送失败";
        setMessagesError(message);
      }
    } finally {
      setIsSending(false);
      setSendingOrigin(null);
      if (origin === "candidate") {
        setCandidateComposerValue("");
      }
      if (origin === "image") {
        setImageComposerValue("");
      }
    }
  }

  async function handleSend(): Promise<void> {
    await handleSendMessage(composerValue, "conversation");
  }

  async function handleCandidateSend(): Promise<void> {
    await handleSendMessage(candidateComposerValue, "candidate");
  }

  async function handleImageSend(): Promise<void> {
    await handleSendMessage(imageComposerValue, "image");
  }

  async function handleGeneratePatternSummary(): Promise<void> {
    await handleSendMessage(GENERATE_PATTERN_SUMMARY_PROMPT);
  }

  async function handleGenerateCopyDraft(): Promise<void> {
    await handleSendMessage(GENERATE_COPY_DRAFT_PROMPT);
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

  async function handleDeleteCandidatePost(postId: string): Promise<void> {
    if (topic === undefined) {
      return;
    }
    const previousPosts = candidatePosts;
    const previousEditorImages = editorImages;
    setCandidatePosts((current) => current.filter((post) => post.id !== postId));
    setEditorImages((current) => current.filter((image) => image.sourcePostId !== postId));
    setMessagesError(null);
    try {
      await deleteCandidatePost(topicId, topic.title, postId);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "删除帖子失败";
      setMessagesError(message);
      setCandidatePosts(previousPosts);
      setEditorImages(previousEditorImages);
    }
  }

  async function handleUploadMaterialImages(files: File[]): Promise<void> {
    if (topic === undefined) {
      return;
    }
    setMessagesError(null);
    const response = await uploadImageMaterials(topicId, topic.title, files);
    setMaterials(response.items);
  }

  async function handleDeleteMaterial(materialId: string): Promise<void> {
    if (topic === undefined) {
      return;
    }
    const previousMaterials = materials;
    const previousEditorImages = editorImages;
    setMaterials((current) => current.filter((item) => item.id !== materialId));
    setEditorImages((current) => current.filter((image) => image.sourceImageId !== materialId));
    setMessagesError(null);
    try {
      await deleteMaterial(topicId, topic.title, materialId);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "删除素材失败";
      setMessagesError(message);
      setMaterials(previousMaterials);
      setEditorImages(previousEditorImages);
    }
  }

  async function handleEditorImagesChange(nextImages: EditorImage[]): Promise<void> {
    if (topic === undefined) {
      return;
    }
    const previousImages = editorImages;
    setEditorImages(nextImages);
    setMessagesError(null);
    try {
      const response = await updateEditorImages(topicId, topic.title, nextImages);
      setEditorImages(response.items);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "保存编辑区图片失败";
      setMessagesError(message);
      setEditorImages(previousImages);
    }
  }

  function handleCopyDraftChange(nextDraft: CopyDraftContent): void {
    setCopyDraft(nextDraft);
    setMessagesError(null);
    if (topic === undefined) {
      return;
    }
    if (copyDraftSaveTimerRef.current !== null) {
      window.clearTimeout(copyDraftSaveTimerRef.current);
    }
    setIsCopyDraftSaving(true);
    copyDraftSaveTimerRef.current = window.setTimeout(() => {
      void (async () => {
        try {
          const response = await updateCopyDraft(topicId, topic.title, nextDraft);
          setCopyDraft(response.copy_draft);
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : "保存文案失败";
          setMessagesError(message);
        } finally {
          setIsCopyDraftSaving(false);
        }
      })();
    }, 280);
  }

  async function handlePolishCopyDraftSelection(payload: {
    selectedText: string;
    instruction: string;
    documentMarkdown: string;
  }): Promise<{ replacementText: string; message: string }> {
    if (topic === undefined) {
      throw new Error("当前没有可编辑的话题");
    }
    const instruction = payload.instruction.trim();
    const timestampLabel = "刚刚";
    const userMessageId = `user-polish:${Date.now()}`;
    const agentMessageId = `agent-polish:${Date.now()}`;

    setMessages((current) => [
      ...current,
      {
        id: userMessageId,
        role: "user",
        text: instruction,
        time: timestampLabel,
      },
    ]);

    try {
      const response = await polishCopyDraftSelection(topicId, topic.title, payload);
      setMessages((current) => [
        ...current,
        {
          id: agentMessageId,
          role: "agent",
          text: response.message,
          time: timestampLabel,
          agentName: "协作 Agent",
        },
      ]);
      void getMessages(topicId, topic.title)
        .then((latestMessages) => {
          setMessages(toChatMessages(latestMessages.messages));
        })
        .catch((error: unknown) => {
          const message = error instanceof Error ? error.message : "加载会话失败";
          setMessagesError(message);
        });
      return {
        replacementText: response.replacement_text,
        message: response.message,
      };
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "AI 润色失败";
      setMessages((current) => [
        ...current,
        {
          id: `${agentMessageId}:failed`,
          role: "agent",
          text: message,
          time: timestampLabel,
          agentName: "协作 Agent",
          status: "failed",
        },
      ]);
      throw error;
    }
  }

  async function handleRemoveGeneratedImage(imageId: string): Promise<void> {
    if (topic === undefined) {
      return;
    }
    const previousResults = imageResults;
    setImageResults((current) => current.filter((item) => item.id !== imageId));
    setMessagesError(null);
    try {
      await deleteImageResult(topicId, topic.title, imageId);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "删除图片结果失败";
      setMessagesError(message);
      setImageResults(previousResults);
    }
  }

  // 从 candidatePosts 收集所有图片作为素材
  const materialImages: MaterialImage[] = useMemo(() => {
    const uploadedImages: MaterialImage[] = materials
      .filter((item) => item.type === "image" && item.imageUrl && item.imagePath)
      .map((item) => ({
        id: item.id,
        sourceImageId: item.id,
        label: item.title || "上传素材",
        imageUrl: item.imageUrl ?? "",
        imagePath: item.imagePath ?? "",
        alt: item.title || "上传素材图片",
      }));
    const postImages: MaterialImage[] = [];
    for (const post of candidatePosts) {
      for (const img of post.images) {
        postImages.push({
          id: `${post.id}-${img.id}`,
          sourceImageId: `${post.id}-${img.id}`,
          sourcePostId: post.id,
          label: post.title,
          imageUrl: img.imageUrl,
          imagePath: img.imagePath,
          alt: img.alt,
        });
      }
    }
    return [...uploadedImages, ...postImages];
  }, [candidatePosts, materials]);

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

  const isCandidateComposerBusy = isSending && sendingOrigin === "candidate";
  const isImageComposerBusy = isSending && sendingOrigin === "image";

  return (
    <motion.main
      animate={{ gridTemplateColumns: shellColumns }}
      className="grid h-screen gap-4 pr-4 pl-0"
      style={{ width: "100%" }}
      data-grid-columns={shellColumns}
      data-left-sidebar={isSidebarCollapsed ? "collapsed" : "open"}
      data-layout="workspace-tabs"
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
        aria-label="工作区主面板"
        className="my-4 flex h-[calc(100vh-2rem)] min-w-0 self-center flex-col overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 shadow-surface"
        data-testid="workspace-main-panel"
      >
        <div className="flex items-center justify-between gap-4 border-b border-slate-100 px-5 py-3">
          <div className="min-w-0">
            <h1 className="truncate text-[24px] font-semibold tracking-[-0.03em] text-slate-950">
              {topic.title}
            </h1>
          </div>
          <div className="flex items-center gap-2">
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

        <div className="border-b border-slate-100 px-4 py-3">
          <div className="flex gap-1 rounded-2xl bg-slate-100/80 p-1">
            {(["创作", "对话"] as const).map((tab) => (
              <button
                aria-pressed={activeContextTab === tab}
                className={`flex-1 rounded-[14px] px-4 py-2 text-sm font-medium transition-colors ${
                  activeContextTab === tab
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
                key={tab}
                onClick={() => setActiveContextTab(tab)}
                type="button"
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="min-h-0 flex-1">
          {activeContextTab === "对话" ? (
            <div
              aria-label="对话工作区"
              className="flex h-full min-h-0 flex-col px-5 py-4"
              data-testid="workspace-conversation-tab"
            >
              <div
                className="scrollbar-subtle min-h-0 flex-1 overflow-y-auto pr-1"
                ref={timelineScrollRef}
              >
                <div className="mx-auto w-full max-w-[840px]">
                  {messagesError ? (
                    <Surface className="mb-4 border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700">
                      {messagesError}
                    </Surface>
                  ) : null}
                  {isMessagesLoading && messages.length === 0 ? (
                    <Surface className="mb-4 p-4 text-sm text-slate-500">正在加载会话...</Surface>
                  ) : null}
                  <AgentTimeline copyDraft={copyDraft} messages={messages} />
                </div>
              </div>

              <div className="mx-auto mt-4 w-full max-w-[840px]">
                <div className="flex items-center gap-3 rounded-[24px] border border-slate-200 bg-slate-50 px-3 py-3 shadow-sm">
                  <textarea
                    aria-label="对话输入框"
                    className="max-h-44 min-h-[44px] flex-1 resize-none overflow-y-auto border-0 bg-transparent px-2 py-[10px] text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400"
                    disabled={isSending}
                    onChange={(event) => setComposerValue(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void handleSend();
                      }
                    }}
                    placeholder="输入你想继续让 Agent 处理的内容..."
                    ref={conversationComposerRef}
                    rows={1}
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
            </div>
          ) : (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              className="scrollbar-subtle h-full overflow-y-auto px-4 py-4"
              initial={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
            >
              <div className="mx-auto flex w-full max-w-6xl flex-col gap-3">
                {activeContextTab === "创作" ? (
                  <>
                    {sectionsById.candidatePosts ? (
                      <ContextPanelGroup
                        expanded={expandedGroups.candidatePosts}
                        onToggle={() => toggleGroup("candidatePosts")}
                        section={sectionsById.candidatePosts}
                      >
                        <CandidatePostsSection
                          onDeletePost={(postId) => void handleDeleteCandidatePost(postId)}
                          posts={candidatePosts}
                        />
                        <div className="mt-4">
                          <InlineRunComposer
                            ariaLabel="搜索结果局部对话输入框"
                            busyText={isCandidateComposerBusy ? "正在搜索..." : undefined}
                            disabled={isCandidateComposerBusy}
                            onChange={setCandidateComposerValue}
                            onSubmit={() => void handleCandidateSend()}
                            placeholder="输入你想继续让agent处理的内容..."
                            value={candidateComposerValue}
                          />
                          {messagesError ? (
                            <p className="mt-2 text-xs text-rose-600">{messagesError}</p>
                          ) : null}
                        </div>

                        <div className="mt-4 border-t border-slate-100 pt-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <h3 className="text-sm font-semibold text-slate-900">总结</h3>
                              <p className="mt-1 text-xs leading-5 text-slate-500">
                                {patternSummary ? "当前总结结果已同步到工作区。" : "还没有总结结果。"}
                              </p>
                            </div>
                            <div className="flex shrink-0 items-center gap-1.5">
                              <Button
                                disabled={isSending}
                                onClick={() => void handleGeneratePatternSummary()}
                                size="sm"
                                type="button"
                                variant="subtle"
                              >
                                {patternSummary ? "重新生成总结" : "生成总结"}
                              </Button>
                              <Button
                                aria-label={`${expandedGroups.patternSummary ? "收起" : "展开"}总结`}
                                aria-expanded={expandedGroups.patternSummary}
                                className="shrink-0"
                                onClick={() => toggleGroup("patternSummary")}
                                size="icon"
                                type="button"
                                variant="ghost"
                              >
                                <ChevronDown
                                  className={`h-4 w-4 transition-transform duration-200 ${
                                    expandedGroups.patternSummary ? "rotate-180" : ""
                                  }`.trim()}
                                  strokeWidth={1.8}
                                />
                              </Button>
                            </div>
                          </div>

                          {expandedGroups.patternSummary ? (
                            <div className="mt-3">
                              {patternSummary ? (
                                <PatternSummarySection content={patternSummary} />
                              ) : (
                                <p className="text-sm text-slate-500">空状态</p>
                              )}
                            </div>
                          ) : null}
                        </div>
                      </ContextPanelGroup>
                    ) : null}

                    {sectionsById.copyDraft ? (
                      <ContextPanelGroup
                        actions={
                          <Button
                            disabled={isSending}
                            onClick={() => void handleGenerateCopyDraft()}
                            size="sm"
                            type="button"
                            variant="subtle"
                          >
                            {copyDraft ? "重新生成文案" : "生成文案"}
                          </Button>
                        }
                        expanded={expandedGroups.copyDraft}
                        onToggle={() => toggleGroup("copyDraft")}
                        section={sectionsById.copyDraft}
                      >
                        <CopyDraftSummaryPanel
                          copyDraft={copyDraft ?? { title: "", body: "" }}
                          isSaving={isCopyDraftSaving}
                          onChange={handleCopyDraftChange}
                          onPolishSelection={handlePolishCopyDraftSelection}
                        />
                      </ContextPanelGroup>
                    ) : null}

                    {sectionsById.imageResults ? (
                      <ContextPanelGroup
                        expanded={expandedGroups.imageResults}
                        onToggle={() => toggleGroup("imageResults")}
                        section={sectionsById.imageResults}
                      >
                        <ImageEditorSection
                          editorImages={editorImages}
                          materialImages={materialImages}
                          onDeleteUploadedImage={(materialId) => void handleDeleteMaterial(materialId)}
                          onEditorImagesChange={(nextImages) =>
                            void handleEditorImagesChange(nextImages)
                          }
                          onUploadImages={(files) => void handleUploadMaterialImages(files)}
                        />
                        <div className="mt-4">
                          <InlineRunComposer
                            ariaLabel="图片局部对话输入框"
                            busyText={isImageComposerBusy ? "图片正在生成..." : undefined}
                            disabled={isImageComposerBusy}
                            onChange={setImageComposerValue}
                            onSubmit={() => void handleImageSend()}
                            placeholder="输入你想继续让agent处理的内容..."
                            value={imageComposerValue}
                          />
                          {messagesError ? (
                            <p className="mt-2 text-xs text-rose-600">{messagesError}</p>
                          ) : null}
                        </div>
                        <div className="mt-4 border-t border-slate-100 pt-4">
                          <p className="mb-2 text-xs font-medium text-slate-500">
                            生成结果 ({imageResults.length})
                          </p>
                          <ImageResultsPanel
                            onRemove={(imageId) => void handleRemoveGeneratedImage(imageId)}
                            results={imageResults}
                          />
                        </div>
                      </ContextPanelGroup>
                    ) : null}
                  </>
                ) : null}
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </motion.main>
  );
}
