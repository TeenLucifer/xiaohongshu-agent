export type SectionStatus = "empty" | "loading" | "success" | "error";

export type WorkspaceSectionId =
  | "materials"
  | "collector"
  | "candidatePosts"
  | "patternSummary"
  | "copyDraft"
  | "imageResults"
  | "conversationTimeline";

export interface TopicCard {
  id: string;
  title: string;
  description: string;
  updatedAt: string;
}

export interface TopicMaterialPreview {
  id: string;
  type: "image" | "text" | "post_link";
  label: string;
  detail: string;
}

export interface WorkspaceSection {
  id: WorkspaceSectionId;
  title: string;
  status: SectionStatus;
  summary: string;
}

export interface TopicWorkspace {
  topic: TopicCard;
  sections: WorkspaceSection[];
}

export interface CandidatePost {
  id: string;
  title: string;
  excerpt: string;
  bodyText: string;
  author: string;
  heat: string;
  sourceUrl: string;
  imageUrl: string;
  selected: boolean;
  manualOrder: number | null;
}

export interface PatternSummaryContent {
  titlePatterns: string[];
  bodyPatterns: string[];
  keywords: string[];
}

export interface CopyDraftContent {
  title: string;
  body: string;
}

export type ImageTaskMode = "text-to-image" | "image-to-image";

export interface ImageCandidate {
  id: string;
  kind: "cover" | "inner";
  alt: string;
  imageUrl: string;
}

export interface ImageTaskGroup {
  id: string;
  mode: ImageTaskMode;
  title: string;
  summary: string;
  images: ImageCandidate[];
}

export type ConversationStatus = "completed" | "running" | "failed";

export interface ConversationEntry {
  id: string;
  time: string;
  agentName: string;
  status: ConversationStatus;
  inputSummary: string;
  outputSummary: string;
  detailLogs: string[];
}

export type ChatMessageRole = "user" | "agent";
export type ChatMessageType = "plain" | "copy";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  text: string;
  time: string;
  agentName?: string;
  type?: ChatMessageType;
}
