import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import {
  mockCandidatePostsByTopicId,
  mockChatMessagesByTopicId,
  mockCopyDraftByTopicId,
  mockPatternSummaryByTopicId,
  mockTopics
} from "../data/mockTopics";

Object.defineProperty(window, "scrollTo", {
  value: vi.fn(),
  writable: true
});

let topicStore = mockTopics.map((topic) => ({ ...topic }));
let candidatePostStore = JSON.parse(JSON.stringify(mockCandidatePostsByTopicId)) as Record<string, typeof mockCandidatePostsByTopicId[string]>;
let patternSummaryStore = JSON.parse(JSON.stringify(mockPatternSummaryByTopicId)) as Record<
  string,
  typeof mockPatternSummaryByTopicId[string] | null
>;
let copyDraftStore = JSON.parse(JSON.stringify(mockCopyDraftByTopicId)) as Record<
  string,
  typeof mockCopyDraftByTopicId[string] | null
>;
let createdTopicCounter = 0;
const mockSkills = [
  {
    name: "xhs-explore",
    description: "搜索与查看小红书帖子。",
    source: "builtin",
    location: "/repo/skills/xiaohongshu-skills/skills/xhs-explore/SKILL.md",
    available: true,
    requires: [],
    content_summary:
      "## 使用方式\n\n- 先读取 `SKILL.md`\n- 再执行搜索与帖子查看流程\n\n> 适合帖子搜集与详情查看。"
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
  candidatePostStore = JSON.parse(JSON.stringify(mockCandidatePostsByTopicId)) as Record<
    string,
    typeof mockCandidatePostsByTopicId[string]
  >;
  patternSummaryStore = JSON.parse(JSON.stringify(mockPatternSummaryByTopicId)) as Record<
    string,
    typeof mockPatternSummaryByTopicId[string] | null
  >;
  copyDraftStore = JSON.parse(JSON.stringify(mockCopyDraftByTopicId)) as Record<
    string,
    typeof mockCopyDraftByTopicId[string] | null
  >;
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
          agent_name: message.agentName ?? null,
          tool_summary: (message.toolSummary ?? []).map((item) => ({
            name: item.name,
            arguments_summary: item.argumentsSummary,
            result_summary: item.resultSummary,
          })),
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
        candidate_posts: candidatePostStore[topicId] ?? [],
        pattern_summary: patternSummaryStore[topicId] ?? null,
        copy_draft: copyDraftStore[topicId] ?? null,
        updated_at: "2026-03-29T10:00:00+08:00"
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/selected-posts") && init?.method === "PUT") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { post_ids?: string[] })
        : {};
    const selectedIds = parsedBody.post_ids ?? [];
    const orderIndex = new Map(selectedIds.map((postId, index) => [postId, index + 1]));
    const currentPosts = candidatePostStore[topicId] ?? [];
    candidatePostStore[topicId] = currentPosts.map((post) => ({
      ...post,
      selected: orderIndex.has(post.id),
      manualOrder: orderIndex.get(post.id) ?? null,
    }));
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: selectedIds.map((postId, index) => ({
          post_id: postId,
          manual_order: index + 1,
        })),
        updated_at: "2026-03-29T10:00:30+08:00",
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
    if (userInput === "请基于当前已选帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。") {
      patternSummaryStore[topicId] = {
        titlePatterns: ["场景切入 + 明确收益"],
        bodyPatterns: ["先代入痛点", "再给出公式", "最后强化收藏理由"],
        keywords: ["通勤", "效率", "基础款", "清单"]
      };
    }
    if (
      userInput ===
      "请基于当前已选帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。"
    ) {
      copyDraftStore[topicId] = {
        title: "早八通勤穿搭别乱买，4 件基础款就够了",
        body:
          "如果你每天早上都在衣柜前发呆，这版思路可以直接照搬。\n\n我把通勤穿搭里最常用的 4 件基础款重新组合了一遍，发现只要把版型和颜色理顺，上班真的会轻松很多。\n\n下面这版公式你可以直接拿去发。"
      };
    }
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
      agent_name: "协作 Agent",
      tool_summary: [
        {
          name: "xhs-explore",
          arguments_summary: `{\"keyword\":${JSON.stringify(userInput)}}`,
          result_summary: "已返回一条运行摘要。"
        }
      ]
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
            agent_name: message.agentName ?? null,
            tool_summary: (message.toolSummary ?? []).map((item) => ({
              name: item.name,
              arguments_summary: item.argumentsSummary,
              result_summary: item.resultSummary,
            })),
          })) as Array<Record<string, unknown>>),
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

  if (path.endsWith("/runs/stream")) {
    const rawBody = init?.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { user_input?: string; topic_title?: string })
        : {};
    const userInput = parsedBody.user_input ?? "";
    if (userInput === "请基于当前已选帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。") {
      patternSummaryStore[topicId] = {
        titlePatterns: ["场景切入 + 明确收益"],
        bodyPatterns: ["先代入痛点", "再给出公式", "最后强化收藏理由"],
        keywords: ["通勤", "效率", "基础款", "清单"]
      };
    }
    if (
      userInput ===
      "请基于当前已选帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。"
    ) {
      copyDraftStore[topicId] = {
        title: "早八通勤穿搭别乱买，4 件基础款就够了",
        body:
          "如果你每天早上都在衣柜前发呆，这版思路可以直接照搬。\n\n我把通勤穿搭里最常用的 4 件基础款重新组合了一遍，发现只要把版型和颜色理顺，上班真的会轻松很多。\n\n下面这版公式你可以直接拿去发。"
      };
    }
    const streamPayload = [
      `event: run_started\ndata: ${JSON.stringify({
        type: "run_started",
        run_id: "run-test",
        timestamp: "2026-03-29T10:01:00+08:00",
        payload: {
          topic_id: topicId,
          session_id: `session-${topicId}`,
        },
      })}\n\n`,
      `event: tool_call_started\ndata: ${JSON.stringify({
        type: "tool_call_started",
        run_id: "run-test",
        timestamp: "2026-03-29T10:01:01+08:00",
        payload: {
          tool_call_id: "call-1",
          name: "xhs-explore",
          arguments_summary: `{\"keyword\":${JSON.stringify(userInput)}}`,
        },
      })}\n\n`,
      `event: tool_call_finished\ndata: ${JSON.stringify({
        type: "tool_call_finished",
        run_id: "run-test",
        timestamp: "2026-03-29T10:01:02+08:00",
        payload: {
          tool_call_id: "call-1",
          name: "xhs-explore",
          arguments_summary: `{\"keyword\":${JSON.stringify(userInput)}}`,
          result_summary: "已返回一条运行摘要。",
        },
      })}\n\n`,
      `event: assistant_delta\ndata: ${JSON.stringify({
        type: "assistant_delta",
        run_id: "run-test",
        timestamp: "2026-03-29T10:01:03+08:00",
        payload: {
          delta: `后端 API mock 已收到：${userInput}`,
        },
      })}\n\n`,
      `event: run_completed\ndata: ${JSON.stringify({
        type: "run_completed",
        run_id: "run-test",
        timestamp: "2026-03-29T10:01:04+08:00",
        payload: {
          topic_id: topicId,
          topic_title: parsedBody.topic_title ?? topic.title,
          session_id: `session-${topicId}`,
          final_text: `后端 API mock 已收到：${userInput}`,
          tool_calls: [
            {
              name: "xhs-explore",
              arguments_summary: `{\"keyword\":${JSON.stringify(userInput)}}`,
              result_summary: "已返回一条运行摘要。",
            },
          ],
          artifacts: [],
        },
      })}\n\n`,
    ].join("");
    return new Response(streamPayload, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" }
    });
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
