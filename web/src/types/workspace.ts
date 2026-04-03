export type SectionStatus = "empty" | "loading" | "success" | "error";

export type WorkspaceSectionId =
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
  images: CandidatePostImage[];
}

export interface CandidatePostImage {
  id: string;
  imageUrl: string;
  imagePath: string;
  alt: string;
}

export interface PatternSummaryContent {
  titlePatterns: string[];
  bodyPatterns: string[];
  keywords: string[];
  imagePatterns: string[];
  imageQualityNotes?: string;
  summaryText?: string;
}

export interface CopyDraftContent {
  title: string;
  body: string;
}

export interface MaterialItem {
  id: string;
  type: "text" | "image" | "link";
  title: string;
  textContent?: string;
  url?: string;
  imageUrl?: string;
  imagePath?: string;
  mimeType?: string;
  createdAt: string;
}

export interface GeneratedImageResult {
  id: string;
  imageUrl: string;
  imagePath: string;
  alt: string;
  prompt: string;
  sourceEditorImageIds: string[];
  createdAt: string;
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

export interface ToolSummaryItem {
  id?: string;
  name: string;
  argumentsSummary: string;
  resultSummary: string;
}

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  text: string;
  time: string;
  agentName?: string;
  type?: ChatMessageType;
  toolSummary?: ToolSummaryItem[];
  imageAttachments?: MessageImageAttachment[];
  status?: "streaming" | "completed" | "failed";
}

export interface MessageImageAttachment {
  imageUrl: string;
  alt: string;
}

// 创作图片区候选图（可能来自上传素材，也可能来自帖子图片）
export interface MaterialImage {
  id: string;
  sourceImageId: string;
  label: string;
  imageUrl: string;
  imagePath: string;
  alt: string;
  sourcePostId?: string;
}

// 编辑区图片（用户选择的图片，带编号）
export interface EditorImage {
  id: string;
  order: number;
  sourceType: "material" | "generated";
  sourcePostId?: string;
  sourceImageId?: string;
  sourceGeneratedImageId?: string;
  imageUrl: string;
  imagePath: string;
  alt: string;
}
