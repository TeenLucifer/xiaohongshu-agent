import type { CandidatePost, ChatMessage, PatternSummaryContent, TopicCard } from "../types/workspace";
import type { SkillListItem } from "../types/skills";

const DEFAULT_API_BASE_URL = "";

export interface ApiChatMessage {
  id: string;
  role: "user" | "agent";
  text: string;
  time: string;
  agent_name?: string | null;
  tool_summary?: Array<{
    name: string;
    arguments_summary: string;
    result_summary: string;
  }>;
}

export interface ApiLastRun {
  final_text: string;
  tool_calls: Array<{
    name: string;
    arguments_summary: string;
    result_summary: string;
  }>;
  artifacts: string[];
}

export interface WorkspaceApiResponse {
  topic_id: string;
  topic_title: string;
  session_id: string;
  messages: ApiChatMessage[];
  updated_at: string;
  last_run?: ApiLastRun | null;
}

export interface RunApiResponse extends WorkspaceApiResponse {
  last_run: ApiLastRun;
  trace_file?: string | null;
}

export type StreamingRunEventType =
  | "run_started"
  | "tool_call_started"
  | "tool_call_finished"
  | "assistant_delta"
  | "run_completed"
  | "run_failed";

export interface StreamingRunEvent {
  type: StreamingRunEventType;
  run_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface MessagesApiResponse {
  topic_id: string;
  topic_title: string;
  session_id: string;
  messages: ApiChatMessage[];
  updated_at: string;
}

export interface WorkspaceContextApiResponse {
  topic_id: string;
  topic_title: string;
  candidate_posts: CandidatePost[];
  pattern_summary: PatternSummaryContent | null;
  updated_at: string;
}

export interface SelectedPostsApiResponse {
  topic_id: string;
  topic_title: string;
  items: Array<{
    post_id: string;
    manual_order: number;
  }>;
  updated_at: string;
}

export interface TopicListItemApiResponse {
  topic_id: string;
  title: string;
  description: string;
  session_id: string;
  updated_at: string;
}

export interface TopicListApiResponse {
  items: TopicListItemApiResponse[];
}

export interface CreateTopicApiResponse {
  topic_id: string;
  title: string;
  description: string;
  session_id: string;
  updated_at: string;
}

export interface DeleteTopicApiResponse {
  deleted_topic_id: string;
}

export interface SkillListItemApiResponse {
  name: string;
  description: string;
  source: string;
  location: string;
  available: boolean;
  requires: string[];
  content_summary: string;
}

export interface SkillsListApiResponse {
  items: SkillListItemApiResponse[];
}

interface ErrorApiResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  return configured && configured.length > 0 ? configured : DEFAULT_API_BASE_URL;
}

function toAbsoluteApiUrl(url: string): string {
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  if (!url.startsWith("/")) {
    return url;
  }
  return `${getApiBaseUrl()}${url}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    let message = "请求失败";
    try {
      const payload = (await response.json()) as ErrorApiResponse;
      message = payload.message || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function toChatMessages(messages: ApiChatMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    text: message.text,
    time: message.time,
    agentName: message.agent_name ?? undefined,
    toolSummary: (message.tool_summary ?? []).map((item) => ({
      name: item.name,
      argumentsSummary: item.arguments_summary,
      resultSummary: item.result_summary,
    })),
  }));
}

export function toTopicCards(items: TopicListItemApiResponse[]): TopicCard[] {
  return items.map((item) => ({
    id: item.topic_id,
    title: item.title,
    description: item.description ?? "",
    updatedAt: item.updated_at,
  }));
}

export async function listTopics(): Promise<TopicListApiResponse> {
  return requestJson<TopicListApiResponse>("/api/topics");
}

export function toSkills(items: SkillListItemApiResponse[]): SkillListItem[] {
  return items.map((item) => ({
    name: item.name,
    description: item.description,
    source: item.source,
    location: item.location,
    available: item.available,
    requires: item.requires ?? [],
    contentSummary: item.content_summary ?? "",
  }));
}

export async function listSkills(): Promise<SkillsListApiResponse> {
  return requestJson<SkillsListApiResponse>("/api/skills");
}

export async function createTopic(title: string, description = ""): Promise<CreateTopicApiResponse> {
  return requestJson<CreateTopicApiResponse>("/api/topics", {
    method: "POST",
    body: JSON.stringify({
      title,
      description,
    }),
  });
}

export async function deleteTopic(topicId: string): Promise<DeleteTopicApiResponse> {
  return requestJson<DeleteTopicApiResponse>(`/api/topics/${topicId}`, {
    method: "DELETE",
  });
}

export async function getWorkspace(topicId: string, topicTitle: string): Promise<WorkspaceApiResponse> {
  const params = new URLSearchParams({ topic_title: topicTitle });
  return requestJson<WorkspaceApiResponse>(`/api/topics/${topicId}/workspace?${params.toString()}`);
}

export async function runTopic(
  topicId: string,
  topicTitle: string,
  userInput: string
): Promise<RunApiResponse> {
  return requestJson<RunApiResponse>(`/api/topics/${topicId}/runs`, {
    method: "POST",
    body: JSON.stringify({
      topic_title: topicTitle,
      user_input: userInput
    })
  });
}

export async function streamTopicRun(
  topicId: string,
  topicTitle: string,
  userInput: string,
  onEvent: (event: StreamingRunEvent) => void
): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/topics/${topicId}/runs/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic_title: topicTitle,
      user_input: userInput,
    }),
  });

  if (!response.ok) {
    let message = "请求失败";
    try {
      const payload = (await response.json()) as ErrorApiResponse;
      message = payload.message || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.body === null) {
    throw new Error("流式响应不可用");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done }).replace(/\r\n/g, "\n");

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawBlock = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 2);
      const event = parseStreamingRunEvent(rawBlock);
      if (event !== null) {
        onEvent(event);
      }
      boundary = buffer.indexOf("\n\n");
    }

    if (done) {
      const trailingEvent = parseStreamingRunEvent(buffer.trim());
      if (trailingEvent !== null) {
        onEvent(trailingEvent);
      }
      break;
    }
  }
}

export async function getMessages(topicId: string, topicTitle: string): Promise<MessagesApiResponse> {
  const params = new URLSearchParams({ topic_title: topicTitle });
  return requestJson<MessagesApiResponse>(`/api/topics/${topicId}/messages?${params.toString()}`);
}

function parseStreamingRunEvent(rawBlock: string): StreamingRunEvent | null {
  if (rawBlock.length === 0) {
    return null;
  }
  const lines = rawBlock.split("\n");
  let eventType: StreamingRunEventType | null = null;
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim() as StreamingRunEventType;
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }
  if (eventType === null || dataLines.length === 0) {
    return null;
  }
  return JSON.parse(dataLines.join("\n")) as StreamingRunEvent;
}

export async function getWorkspaceContext(
  topicId: string,
  topicTitle: string
): Promise<WorkspaceContextApiResponse> {
  const params = new URLSearchParams({ topic_title: topicTitle });
  const response = await requestJson<WorkspaceContextApiResponse>(
    `/api/topics/${topicId}/context?${params.toString()}`
  );
  return {
    ...response,
    candidate_posts: response.candidate_posts.map((post) => ({
      ...post,
      imageUrl: toAbsoluteApiUrl(post.imageUrl),
      images: (post.images ?? []).map((image) => ({
        ...image,
        imageUrl: toAbsoluteApiUrl(image.imageUrl)
      }))
    }))
  };
}

export async function updateSelectedPosts(
  topicId: string,
  topicTitle: string,
  postIds: string[]
): Promise<SelectedPostsApiResponse> {
  return requestJson<SelectedPostsApiResponse>(`/api/topics/${topicId}/selected-posts`, {
    method: "PUT",
    body: JSON.stringify({
      topic_title: topicTitle,
      post_ids: postIds
    })
  });
}

export async function resetTopic(topicId: string, topicTitle: string): Promise<WorkspaceApiResponse> {
  return requestJson<WorkspaceApiResponse>(`/api/topics/${topicId}/reset`, {
    method: "POST",
    body: JSON.stringify({
      topic_title: topicTitle
    })
  });
}
