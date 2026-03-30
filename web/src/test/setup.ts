import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import {
  mockCandidatePostsByTopicId,
  mockChatMessagesByTopicId,
  mockPatternSummaryByTopicId,
  mockTopics
} from "../data/mockTopics";

Object.defineProperty(window, "scrollTo", {
  value: vi.fn(),
  writable: true
});

let topicStore = mockTopics.map((topic) => ({ ...topic }));
let createdTopicCounter = 0;
const mockSkills = [
  {
    name: "xhs-explore",
    description: "搜索与查看小红书帖子。",
    source: "builtin",
    location: "/repo/skills/xiaohongshu-skills/skills/xhs-explore/SKILL.md",
    available: true,
    requires: [],
    content_summary: "先读取 SKILL.md，再执行搜索与帖子查看流程。"
  },
  {
    name: "xhs-auth",
    description: "账号与登录相关能力。",
    source: "builtin",
    location: "/repo/skills/xiaohongshu-skills/skills/xhs-auth/SKILL.md",
    available: false,
    requires: ["ENV: XHS_COOKIE"],
    content_summary: "用于账号登录状态确认和鉴权。"
  }
];

beforeEach(() => {
  topicStore = mockTopics.map((topic) => ({ ...topic }));
  createdTopicCounter = 0;
});

const defaultFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
  const requestUrl = new URL(url, "http://127.0.0.1:8000");
  const path = requestUrl.pathname;
  const topicId = path.split("/")[3] ?? topicStore[0]?.id ?? mockTopics[0].id;
  const topic = topicStore.find((item) => item.id === topicId) ?? mockTopics[0];

  if (path === "/api/topics" && (init?.method === undefined || init.method === "GET")) {
    return new Response(
      JSON.stringify({
        items: topicStore.map((item) => ({
          topic_id: item.id,
          title: item.title,
          description: item.description,
          session_id: `session-${item.id}`,
          updated_at: item.updatedAt
        }))
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path === "/api/skills" && (init?.method === undefined || init.method === "GET")) {
    return new Response(
      JSON.stringify({
        items: mockSkills
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path === "/api/topics" && init?.method === "POST") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { title?: string; description?: string })
        : {};
    createdTopicCounter += 1;
    const topicIdValue = `topic_01TESTTOPIC${String(createdTopicCounter).padStart(10, "0")}`;
    const createdTopic = {
      id: topicIdValue,
      title: parsedBody.title ?? "新建话题",
      description: parsedBody.description ?? "",
      updatedAt: "2026-03-30T10:00:00+08:00"
    };
    topicStore = [createdTopic, ...topicStore];
    return new Response(
      JSON.stringify({
        topic_id: createdTopic.id,
        title: createdTopic.title,
        description: createdTopic.description,
        session_id: `session-${createdTopic.id}`,
        updated_at: createdTopic.updatedAt
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.startsWith("/api/topics/") && init?.method === "DELETE") {
    const deletingTopicId = path.split("/")[3] ?? "";
    topicStore = topicStore.filter((item) => item.id !== deletingTopicId);
    return new Response(
      JSON.stringify({
        deleted_topic_id: deletingTopicId
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/workspace") || path.endsWith("/messages")) {
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: requestUrl.searchParams.get("topic_title") ?? topic.title,
        session_id: `session-${topicId}`,
        messages: (mockChatMessagesByTopicId[topicId] ?? []).map((message) => ({
          id: message.id,
          role: message.role,
          text: message.text,
          time: message.time,
          agent_name: message.agentName ?? null
        })),
        updated_at: "2026-03-29T10:00:00+08:00",
        last_run: null
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/context")) {
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: requestUrl.searchParams.get("topic_title") ?? topic.title,
        candidate_posts: mockCandidatePostsByTopicId[topicId] ?? [],
        pattern_summary: mockPatternSummaryByTopicId[topicId] ?? null,
        updated_at: "2026-03-29T10:00:00+08:00"
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/runs")) {
    const rawBody = init?.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { user_input?: string; topic_title?: string })
        : {};
    const userInput = parsedBody.user_input ?? "";
    const userMessage = {
      id: `user-${userInput}`,
      role: "user",
      text: userInput,
      time: "刚刚",
      agent_name: null
    };
    const agentMessage = {
      id: `agent-${userInput}`,
      role: "agent",
      text: `后端 API mock 已收到：${userInput}`,
      time: "刚刚",
      agent_name: "协作 Agent"
    };
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: parsedBody.topic_title ?? topic.title,
        session_id: `session-${topicId}`,
        messages: [
          ...((mockChatMessagesByTopicId[topicId] ?? []).map((message) => ({
            id: message.id,
            role: message.role,
            text: message.text,
            time: message.time,
            agent_name: message.agentName ?? null
          })) as Array<Record<string, string | null>>),
          userMessage,
          agentMessage
        ],
        updated_at: "2026-03-29T10:01:00+08:00",
        last_run: {
          final_text: agentMessage.text,
          tool_calls: [],
          artifacts: []
        }
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/reset")) {
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        session_id: `session-${topicId}`,
        messages: [],
        updated_at: "2026-03-29T10:02:00+08:00"
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  return new Response(JSON.stringify({ message: `Unhandled fetch in test: ${path}` }), {
    status: 500,
    headers: { "Content-Type": "application/json" }
  });
});

Object.defineProperty(globalThis, "fetch", {
  value: defaultFetch,
  writable: true
});
