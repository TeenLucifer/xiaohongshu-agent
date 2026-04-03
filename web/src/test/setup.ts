import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
import {
  mockCandidatePostsByTopicId,
  mockChatMessagesByTopicId,
  mockCopyDraftByTopicId,
  mockImageResultsByTopicId,
  mockPatternSummaryByTopicId,
  mockTopics
} from "../data/mockTopics";

Object.defineProperty(window, "scrollTo", {
  value: vi.fn(),
  writable: true
});

if (typeof Element !== "undefined") {
  Object.defineProperty(Element.prototype, "scrollIntoView", {
    configurable: true,
    value: vi.fn(),
  });
}

if (typeof Range !== "undefined") {
  Object.defineProperty(Range.prototype, "getBoundingClientRect", {
    configurable: true,
    value: () => ({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      width: 0,
      height: 0,
      toJSON: () => ({})
    })
  });
  Object.defineProperty(Range.prototype, "getClientRects", {
    configurable: true,
    value: () =>
      ({
        item: () => null,
        length: 0,
        [Symbol.iterator]: function* () {
          return;
        }
      }) as DOMRectList
  });
}

let topicStore = mockTopics.map((topic) => ({ ...topic }));
let candidatePostStore = JSON.parse(JSON.stringify(mockCandidatePostsByTopicId)) as Record<string, typeof mockCandidatePostsByTopicId[string]>;
let messageStore = JSON.parse(JSON.stringify(mockChatMessagesByTopicId)) as Record<
  string,
  typeof mockChatMessagesByTopicId[string]
>;
let patternSummaryStore = JSON.parse(JSON.stringify(mockPatternSummaryByTopicId)) as Record<
  string,
  typeof mockPatternSummaryByTopicId[string] | null
>;
let copyDraftStore = JSON.parse(JSON.stringify(mockCopyDraftByTopicId)) as Record<
  string,
  typeof mockCopyDraftByTopicId[string] | null
>;
let materialsStore = {} as Record<string, Array<Record<string, unknown>>>;
let editorImagesStore = {} as Record<string, Array<Record<string, unknown>>>;
let imageResultsStore = JSON.parse(JSON.stringify(mockImageResultsByTopicId)) as Record<
  string,
  typeof mockImageResultsByTopicId[string]
>;
let settingsStore = {
  llm: {
    base_url: "https://api.openai.com/v1",
    model: "gpt-5.4",
    api_key: "sk-llm-test-key",
  },
  image_analysis: {
    base_url: "https://api.siliconflow.cn/v1",
    model: "Qwen/Qwen2.5-VL-32B-Instruct",
    api_key: "sk-vision-test-key",
  },
  image_generation: {
    base_url: "https://aihubmix.com/v1",
    model: "gemini-2.5-flash-image-preview",
    api_key: "sk-image-test-key",
  },
};
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
  messageStore = JSON.parse(JSON.stringify(mockChatMessagesByTopicId)) as Record<
    string,
    typeof mockChatMessagesByTopicId[string]
  >;
  patternSummaryStore = JSON.parse(JSON.stringify(mockPatternSummaryByTopicId)) as Record<
    string,
    typeof mockPatternSummaryByTopicId[string] | null
  >;
  copyDraftStore = JSON.parse(JSON.stringify(mockCopyDraftByTopicId)) as Record<
    string,
    typeof mockCopyDraftByTopicId[string] | null
  >;
  materialsStore = {};
  editorImagesStore = {};
  imageResultsStore = JSON.parse(JSON.stringify(mockImageResultsByTopicId)) as Record<
    string,
    typeof mockImageResultsByTopicId[string]
  >;
  settingsStore = {
    llm: {
      base_url: "https://api.openai.com/v1",
      model: "gpt-5.4",
      api_key: "sk-llm-test-key",
    },
    image_analysis: {
      base_url: "https://api.siliconflow.cn/v1",
      model: "Qwen/Qwen2.5-VL-32B-Instruct",
      api_key: "sk-vision-test-key",
    },
    image_generation: {
      base_url: "https://aihubmix.com/v1",
      model: "gemini-2.5-flash-image-preview",
      api_key: "sk-image-test-key",
    },
  };
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

  if (path === "/api/settings" && (init?.method === undefined || init.method === "GET")) {
    return new Response(
      JSON.stringify({
        llm: {
          base_url: settingsStore.llm.base_url,
          model: settingsStore.llm.model,
          api_key: settingsStore.llm.api_key,
          api_key_configured: settingsStore.llm.api_key.length > 0,
          api_key_masked: settingsStore.llm.api_key.length > 0 ? "sk-llm...-key" : null,
        },
        image_analysis: {
          base_url: settingsStore.image_analysis.base_url,
          model: settingsStore.image_analysis.model,
          api_key: settingsStore.image_analysis.api_key,
          api_key_configured: settingsStore.image_analysis.api_key.length > 0,
          api_key_masked:
            settingsStore.image_analysis.api_key.length > 0 ? "sk-vis...-key" : null,
        },
        image_generation: {
          base_url: settingsStore.image_generation.base_url,
          model: settingsStore.image_generation.model,
          api_key: settingsStore.image_generation.api_key,
          api_key_configured: settingsStore.image_generation.api_key.length > 0,
          api_key_masked:
            settingsStore.image_generation.api_key.length > 0 ? "sk-img...-key" : null,
        },
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (/^\/api\/settings\/(llm|image-analysis|image-generation)$/.test(path) && init?.method === "PUT") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { base_url?: string; model?: string; api_key?: string | null })
        : {};
    const target =
      path.endsWith("/llm")
        ? settingsStore.llm
        : path.endsWith("/image-analysis")
          ? settingsStore.image_analysis
          : settingsStore.image_generation;
    target.base_url = parsedBody.base_url ?? target.base_url;
    target.model = parsedBody.model ?? target.model;
    if (parsedBody.api_key !== undefined && parsedBody.api_key !== null) {
      target.api_key = parsedBody.api_key;
    }

    const masked =
      target.api_key.length > 0
        ? target === settingsStore.llm
          ? "sk-llm...-key"
          : target === settingsStore.image_analysis
            ? "sk-vis...-key"
            : "sk-img...-key"
        : null;

    return new Response(
      JSON.stringify({
        base_url: target.base_url,
        model: target.model,
        api_key: target.api_key,
        api_key_configured: target.api_key.length > 0,
        api_key_masked: masked,
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (
    /^\/api\/settings\/(llm|image-analysis|image-generation)\/test$/.test(path) &&
    init?.method === "POST"
  ) {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { base_url?: string; model?: string; api_key?: string | null })
        : {};
    const target =
      path.includes("/llm/")
        ? settingsStore.llm
        : path.includes("/image-analysis/")
          ? settingsStore.image_analysis
          : settingsStore.image_generation;
    const hasBaseUrl = Boolean(parsedBody.base_url?.trim());
    const hasModel = Boolean(parsedBody.model?.trim());
    const hasApiKey = Boolean(parsedBody.api_key?.trim()) || target.api_key.trim().length > 0;

    if (!hasBaseUrl || !hasModel || !hasApiKey) {
      return new Response(
        JSON.stringify({
          message: "测试配置不完整",
        }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" }
        }
      );
    }

    const successMessage = path.endsWith("/llm/test")
      ? "主 LLM 连接成功。"
      : path.endsWith("/image-analysis/test")
        ? "图片识别连接成功。"
        : "图片生成连接成功。";
    return new Response(
      JSON.stringify({
        success: true,
        message: successMessage,
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

  if (/^\/api\/topics\/[^/]+$/.test(path) && init?.method === "DELETE") {
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
        messages: (messageStore[topicId] ?? []).map((message) => ({
          id: message.id,
          role: message.role,
          text: message.text,
          time: message.time,
          agent_name: message.agentName ?? null,
          image_attachments: (message.imageAttachments ?? []).map((image) => ({
            image_url: image.imageUrl,
            alt: image.alt,
          })),
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
        materials: materialsStore[topicId] ?? [],
        candidate_posts: candidatePostStore[topicId] ?? [],
        pattern_summary: patternSummaryStore[topicId] ?? null,
        copy_draft: copyDraftStore[topicId] ?? null,
        editor_images: editorImagesStore[topicId] ?? [],
        image_results: imageResultsStore[topicId] ?? [],
        updated_at: "2026-03-29T10:00:00+08:00"
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/editor-images") && (init?.method === undefined || init.method === "GET")) {
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: editorImagesStore[topicId] ?? [],
        updated_at: "2026-03-29T10:00:30+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/materials") && (init?.method === undefined || init.method === "GET")) {
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: materialsStore[topicId] ?? [],
        updated_at: "2026-03-29T10:00:20+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/materials/text") && init?.method === "POST") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { title?: string; text_content?: string; textContent?: string })
        : {};
    const nextItem = {
      id: `material-text-${Date.now()}`,
      type: "text",
      title: parsedBody.title ?? "",
      textContent: parsedBody.text_content ?? parsedBody.textContent ?? "",
      createdAt: "2026-03-29T10:00:21+08:00",
    };
    materialsStore[topicId] = [...(materialsStore[topicId] ?? []), nextItem];
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: materialsStore[topicId],
        updated_at: "2026-03-29T10:00:21+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/materials/link") && init?.method === "POST") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { title?: string; url?: string })
        : {};
    const nextItem = {
      id: `material-link-${Date.now()}`,
      type: "link",
      title: parsedBody.title ?? "",
      url: parsedBody.url ?? "",
      createdAt: "2026-03-29T10:00:22+08:00",
    };
    materialsStore[topicId] = [...(materialsStore[topicId] ?? []), nextItem];
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: materialsStore[topicId],
        updated_at: "2026-03-29T10:00:22+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/materials/images") && init?.method === "POST") {
    const nextItems = [
      {
        id: `material-image-${Date.now()}`,
        type: "image",
        title: "上传素材",
        imageUrl: `https://example.com/material-${Date.now()}.png`,
        imagePath: `materials/material-${Date.now()}.png`,
        createdAt: "2026-03-29T10:00:23+08:00",
      },
    ];
    materialsStore[topicId] = [...(materialsStore[topicId] ?? []), ...nextItems];
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: materialsStore[topicId],
        updated_at: "2026-03-29T10:00:23+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/editor-images") && init?.method === "PUT") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { items?: Array<Record<string, unknown>> })
        : {};
    editorImagesStore[topicId] = (parsedBody.items ?? []).map((item, index) => ({
      id: item.id ?? `editor-${index + 1}`,
      order: index + 1,
      sourceType: item.source_type ?? item.sourceType ?? "material",
      sourcePostId: item.source_post_id ?? item.sourcePostId ?? null,
      sourceImageId: item.source_image_id ?? item.sourceImageId ?? null,
      sourceGeneratedImageId:
        item.source_generated_image_id ?? item.sourceGeneratedImageId ?? null,
      imageUrl: `/api/topics/${topicId}/assets/${String(item.image_path ?? item.imagePath ?? "")}`,
      imagePath: String(item.image_path ?? item.imagePath ?? ""),
      alt: item.alt ?? `编辑图 ${index + 1}`,
    }));
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        items: editorImagesStore[topicId],
        updated_at: "2026-03-29T10:00:40+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/copy-draft") && init?.method === "PUT") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as { title?: string; body?: string })
        : {};
    copyDraftStore[topicId] = {
      title: parsedBody.title ?? "",
      body: parsedBody.body ?? "",
    };
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        copy_draft: copyDraftStore[topicId],
        updated_at: "2026-03-29T10:00:42+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.endsWith("/copy-draft/polish-selection") && init?.method === "POST") {
    const rawBody = init.body;
    const parsedBody =
      typeof rawBody === "string"
        ? (JSON.parse(rawBody) as {
            selected_text?: string;
            instruction?: string;
            document_markdown?: string;
          })
        : {};
    const selectedText = parsedBody.selected_text ?? "";
    const instruction = parsedBody.instruction ?? "";
    const replacementText = `[已润色] ${selectedText || "选中文本"}`;
    messageStore[topicId] = [
      ...(messageStore[topicId] ?? []),
      {
        id: `agent-polish-${Date.now()}`,
        role: "agent",
        text: `已按要求润色选中文本：${instruction || "未提供要求"}`,
        time: "刚刚",
        agentName: "协作 Agent",
      },
    ];
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: topic.title,
        replacement_text: replacementText,
        message: `已按要求润色选中文本：${instruction || "未提供要求"}`,
        updated_at: "2026-03-29T10:00:43+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.includes("/image-results/") && init?.method === "DELETE") {
    const pathParts = path.split("/");
    const imageId = pathParts[pathParts.length - 1] ?? "";
    imageResultsStore[topicId] = (imageResultsStore[topicId] ?? []).filter((item) => item.id !== imageId);
    return new Response(
      JSON.stringify({
        deleted_image_id: imageId,
        updated_at: "2026-03-29T10:00:45+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.includes("/materials/") && init?.method === "DELETE") {
    const pathParts = path.split("/");
    const materialId = pathParts[pathParts.length - 1] ?? "";
    materialsStore[topicId] = (materialsStore[topicId] ?? []).filter((item) => item.id !== materialId);
    editorImagesStore[topicId] = (editorImagesStore[topicId] ?? []).filter(
      (item) => item.sourceImageId !== materialId && item.source_image_id !== materialId
    );
    return new Response(
      JSON.stringify({
        deleted_material_id: materialId,
        updated_at: "2026-03-29T10:00:44+08:00",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }

  if (path.includes("/posts/") && init?.method === "DELETE") {
    const pathParts = path.split("/");
    const postId = pathParts[pathParts.length - 1] ?? "";
    candidatePostStore[topicId] = (candidatePostStore[topicId] ?? []).filter((item) => item.id !== postId);
    editorImagesStore[topicId] = (editorImagesStore[topicId] ?? []).filter(
      (item) => item.sourcePostId !== postId && item.source_post_id !== postId
    );
    return new Response(
      JSON.stringify({
        deleted_post_id: postId,
        updated_at: "2026-03-29T10:00:46+08:00",
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
    if (userInput === "请基于当前保留帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。") {
      patternSummaryStore[topicId] = {
        titlePatterns: ["场景切入 + 明确收益"],
        bodyPatterns: ["先代入痛点", "再给出公式", "最后强化收藏理由"],
        keywords: ["通勤", "效率", "基础款", "清单"],
        imagePatterns: []
      };
    }
    if (
      userInput ===
      "请基于当前保留帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。"
    ) {
      copyDraftStore[topicId] = {
        title: "早八通勤穿搭别乱买，4 件基础款就够了",
        body:
          "如果你每天早上都在衣柜前发呆，这版思路可以直接照搬。\n\n我把通勤穿搭里最常用的 4 件基础款重新组合了一遍，发现只要把版型和颜色理顺，上班真的会轻松很多。\n\n下面这版公式你可以直接拿去发。"
      };
    }
    const generatedImageAttachment =
      userInput.includes("生成图片") || userInput.includes("1号图") || userInput.includes("2号图")
        ? [
            {
              image_url: "https://example.com/generated-result.png",
              alt: "生成结果图",
            },
          ]
        : [];
    if (generatedImageAttachment.length > 0) {
      imageResultsStore[topicId] = [
        ...(imageResultsStore[topicId] ?? []),
        {
          id: `gen-${Date.now()}`,
          imageUrl: "https://example.com/generated-result.png",
          imagePath: "generated_images/generated-result.png",
          alt: "生成结果图",
          prompt: userInput,
          sourceEditorImageIds: [],
          createdAt: "2026-03-29T10:00:50+08:00",
        },
      ];
    }
    const userMessage = {
      id: `user-${userInput}`,
      role: "user",
      text: userInput,
      time: "刚刚",
    };
    const agentMessage = {
      id: `agent-${userInput}`,
      role: "agent",
      text: `后端 API mock 已收到：${userInput}`,
      time: "刚刚",
      agent_name: "协作 Agent",
      image_attachments: generatedImageAttachment,
      tool_summary: [
        {
          name: "xhs-explore",
          arguments_summary: `{\"keyword\":${JSON.stringify(userInput)}}`,
          result_summary: "已返回一条运行摘要。"
        }
      ]
    };
    messageStore[topicId] = [
      ...(messageStore[topicId] ?? []),
      {
        id: userMessage.id,
        role: "user",
        text: userMessage.text,
        time: userMessage.time,
      },
      {
        id: agentMessage.id,
        role: "agent",
        text: agentMessage.text,
        time: agentMessage.time,
        agentName: "协作 Agent",
        toolSummary: [
          {
            name: "xhs-explore",
            argumentsSummary: `{\"keyword\":${JSON.stringify(userInput)}}`,
            resultSummary: "已返回一条运行摘要。",
          },
        ],
        imageAttachments: generatedImageAttachment.map((image) => ({
          imageUrl: image.image_url,
          alt: image.alt,
        })),
      },
    ];
    return new Response(
      JSON.stringify({
        topic_id: topicId,
        topic_title: parsedBody.topic_title ?? topic.title,
        session_id: `session-${topicId}`,
        messages: [
          ...((messageStore[topicId] ?? []).map((message) => ({
            id: message.id,
            role: message.role,
            text: message.text,
            time: message.time,
            agent_name: message.agentName ?? null,
            image_attachments: (message.imageAttachments ?? []).map((image) => ({
              image_url: image.imageUrl,
              alt: image.alt,
            })),
            tool_summary: (message.toolSummary ?? []).map((item) => ({
              name: item.name,
              arguments_summary: item.argumentsSummary,
              result_summary: item.resultSummary,
            })),
          })) as Array<Record<string, unknown>>)
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
    if (userInput === "请基于当前保留帖子，生成一份结构化总结，并写入当前 workspace 的 pattern_summary.json。") {
      patternSummaryStore[topicId] = {
        titlePatterns: ["场景切入 + 明确收益"],
        bodyPatterns: ["先代入痛点", "再给出公式", "最后强化收藏理由"],
        keywords: ["通勤", "效率", "基础款", "清单"],
        imagePatterns: []
      };
    }
    if (
      userInput ===
      "请基于当前保留帖子和当前 workspace 中的 pattern_summary.json，生成一版文案，并写入当前 workspace 的 copy_draft.json。"
    ) {
      copyDraftStore[topicId] = {
        title: "早八通勤穿搭别乱买，4 件基础款就够了",
        body:
          "如果你每天早上都在衣柜前发呆，这版思路可以直接照搬。\n\n我把通勤穿搭里最常用的 4 件基础款重新组合了一遍，发现只要把版型和颜色理顺，上班真的会轻松很多。\n\n下面这版公式你可以直接拿去发。"
      };
    }
    if (userInput.includes("生成图片") || userInput.includes("1号图") || userInput.includes("2号图")) {
      imageResultsStore[topicId] = [
        ...(imageResultsStore[topicId] ?? []),
        {
          id: `gen-stream-${Date.now()}`,
          imageUrl: "https://example.com/generated-result.png",
          imagePath: "generated_images/generated-result.png",
          alt: "生成结果图",
          prompt: userInput,
          sourceEditorImageIds: [],
          createdAt: "2026-03-29T10:00:50+08:00",
        },
      ];
    }
    messageStore[topicId] = [
      ...(messageStore[topicId] ?? []),
      {
        id: `user-${userInput}`,
        role: "user",
        text: userInput,
        time: "刚刚",
      },
      {
        id: `agent-${userInput}`,
        role: "agent",
        text: `后端 API mock 已收到：${userInput}`,
        time: "刚刚",
        agentName: "协作 Agent",
        toolSummary: [
          {
            name: "xhs-explore",
            argumentsSummary: `{\"keyword\":${JSON.stringify(userInput)}}`,
            resultSummary: "已返回一条运行摘要。",
          },
        ],
      },
    ];
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
