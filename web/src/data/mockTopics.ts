import type {
  CandidatePost,
  ChatMessage,
  ConversationEntry,
  CopyDraftContent,
  GeneratedImageResult,
  PatternSummaryContent,
  TopicCard,
  TopicMaterialPreview,
  TopicWorkspace
} from "../types/workspace";

function createSvgCover(label: string, startColor: string, endColor: string): string {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${startColor}" />
          <stop offset="100%" stop-color="${endColor}" />
        </linearGradient>
      </defs>
      <rect width="640" height="400" rx="36" fill="url(#bg)" />
      <text x="56" y="168" font-size="42" fill="#ffffff" font-family="Arial, sans-serif">${label}</text>
    </svg>
  `;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function buildCandidateImages(...urls: string[]) {
  return urls.map((imageUrl, index) => ({
    id: `image-${index + 1}`,
    imageUrl,
    imagePath: imageUrl.startsWith("/") ? imageUrl.slice(1) : imageUrl,
    alt: `候选帖图片 ${index + 1}`
  }));
}

export const mockTopics: TopicCard[] = [
  {
    id: "topic-spring-commute",
    title: "春季通勤穿搭",
    description: "围绕春季上班场景，整理适合都市白领的小红书内容方向。",
    updatedAt: "今天 14:30"
  },
  {
    id: "topic-small-rental",
    title: "租房小户型改造",
    description: "围绕低预算改造和空间收纳，整理高互动图文思路。",
    updatedAt: "昨天 20:15"
  }
];

export const mockWorkspaces: Record<string, TopicWorkspace> = {
  "topic-spring-commute": {
    topic: mockTopics[0],
    sections: [
      { id: "materials", title: "素材", status: "success", summary: "已上传 3 份素材。" },
      { id: "collector", title: "搜集", status: "loading", summary: "搜集中，已返回 3 条高相关候选帖子。" },
      { id: "candidatePosts", title: "搜索结果", status: "success", summary: "默认展开，支持详情查看与加入已选。" },
      { id: "patternSummary", title: "总结", status: "success", summary: "模式总结已融入中间对话流。" },
      { id: "copyDraft", title: "文案", status: "success", summary: "当前文案支持在中栏进入编辑态。" },
      { id: "imageResults", title: "图片", status: "success", summary: "封面与内页候选图已生成。" },
      { id: "conversationTimeline", title: "对话", status: "success", summary: "主栏仅展示 user / agent 对话。" }
    ]
  },
  "topic-small-rental": {
    topic: mockTopics[1],
    sections: [
      { id: "materials", title: "素材", status: "empty", summary: "当前还没有上传素材。" },
      { id: "collector", title: "搜集", status: "empty", summary: "等待开始搜集。" },
      { id: "candidatePosts", title: "搜索结果", status: "empty", summary: "还没有候选帖子。" },
      { id: "patternSummary", title: "总结", status: "empty", summary: "还没有总结结果。" },
      { id: "copyDraft", title: "文案", status: "empty", summary: "还没有文案草稿。" },
      { id: "imageResults", title: "图片", status: "empty", summary: "还没有图片结果。" },
      { id: "conversationTimeline", title: "对话", status: "empty", summary: "还没有会话记录。" }
    ]
  }
};

export const mockCandidatePostsByTopicId: Record<string, CandidatePost[]> = {
  "topic-spring-commute": [
    {
      id: "candidate-suit-looks",
      title: "春日通勤西装 3 套搭法",
      excerpt: "偏日常的西装通勤思路，强调低门槛叠穿和颜色统一，适合上班族直接参考。",
      bodyText:
        "如果你春天上班总觉得西装太正式、针织又容易没精神，这条笔记的思路很适合直接借鉴。作者把一件浅灰西装拆成三套通勤搭法，重点不是买新衣服，而是把现有基础款通过内搭颜色和鞋包统一起来。正文节奏也很标准，先讲早八通勤的穿衣痛点，再给出 3 套可照搬公式，最后补充身高和版型建议，收藏价值很强。",
      author: "通勤研究所",
      heat: "收藏 3.2w · 点赞 1.6w",
      sourceUrl: "https://www.xiaohongshu.com/explore/suit-looks",
      imageUrl: "/references/ScreenShot_2026-03-26_201829_887.png",
      images: buildCandidateImages(
        "/references/ScreenShot_2026-03-26_201829_887.png",
        createSvgCover("西装细节", "#c0d0ec", "#6f85b5"),
        createSvgCover("搭配公式", "#dfbca6", "#8e5c42")
      ),
      selected: true,
      manualOrder: 1
    },
    {
      id: "candidate-makeup-outfit",
      title: "早八不费力通勤妆 + 穿搭",
      excerpt: "把妆容和穿搭合并成一个完整通勤方案，标题切中效率场景，图文节奏很适合模仿。",
      bodyText:
        "这条内容把妆容和穿搭合在同一篇里，整体很像小红书里容易出高互动的生活方式笔记。开头先用“早八时间不够”切场景，中间分别拆妆容步骤和通勤单品组合，最后再给出一个 10 分钟完成版本。它的优势不是信息量最大，而是执行门槛很低，读完就能直接照着做。",
      author: "晨间造型室",
      heat: "收藏 2.4w · 点赞 1.1w",
      sourceUrl: "https://www.xiaohongshu.com/explore/makeup-outfit",
      imageUrl: createSvgCover("通勤妆容", "#f7b3b7", "#d65978"),
      images: buildCandidateImages(
        createSvgCover("通勤妆容", "#f7b3b7", "#d65978"),
        createSvgCover("妆容步骤", "#f0c2d3", "#c56d90")
      ),
      selected: false,
      manualOrder: null
    },
    {
      id: "candidate-budget-closet",
      title: "低预算通勤衣橱整理术",
      excerpt: "通过基础单品复用来解决春季通勤搭配问题，评论区互动很强，适合做结构参考。",
      bodyText:
        "这篇笔记更偏“方法论”而不是单套穿搭展示，适合拿来做结构参考。作者先列了通勤衣橱最值得保留的 4 类基础单品，再展示不同天气下的搭配替换方式。评论区里很多用户会讨论自己的衣橱问题，所以它在互动上很强，也适合作为模式总结的样本。",
      author: "衣橱效率派",
      heat: "收藏 2.9w · 点赞 1.3w",
      sourceUrl: "https://www.xiaohongshu.com/explore/budget-closet",
      imageUrl: createSvgCover("衣橱整理", "#ffc76e", "#b86d06"),
      images: buildCandidateImages(
        createSvgCover("衣橱整理", "#ffc76e", "#b86d06"),
        createSvgCover("基础单品", "#ffdca7", "#c98727")
      ),
      selected: true,
      manualOrder: 2
    },
    {
      id: "candidate-cardigan",
      title: "薄针织 + 西裤，通勤一周不重样",
      excerpt: "很适合做标题节奏参考。",
      bodyText:
        "标题非常直接，正文把每天的出勤场景拆得很细，适合拿来做节奏参考。它的封面语义也比较明确：一眼就知道是通勤场景而不是模特大片。",
      author: "衣着整理局",
      heat: "收藏 1.8w · 点赞 9.6k",
      sourceUrl: "https://www.xiaohongshu.com/explore/cardigan-week",
      imageUrl: createSvgCover("薄针织", "#abc6ea", "#5674b8"),
      images: buildCandidateImages(createSvgCover("薄针织", "#abc6ea", "#5674b8")),
      selected: false,
      manualOrder: null
    }
  ],
  "topic-small-rental": []
};

export const mockMaterialPreviewByTopicId: Record<string, TopicMaterialPreview[]> = {
  "topic-spring-commute": [
    { id: "material-image-1", type: "image", label: "通勤穿搭灵感图", detail: "用户上传图片 · 2 张" },
    { id: "material-text-1", type: "text", label: "选题要求", detail: "强调低预算、适合早八、避免过度精致感" },
    { id: "material-link-1", type: "post_link", label: "参考帖子链接", detail: "只作为搜集方向，不直接进入候选池" }
  ],
  "topic-small-rental": []
};

export const mockPatternSummaryByTopicId: Record<string, PatternSummaryContent> = {
  "topic-spring-commute": {
    titlePatterns: ["场景 + 痛点 + 解决方案", "低预算 + 高效率 + 通勤"],
    bodyPatterns: ["开头代入上班焦虑", "中段给出搭配公式", "结尾用清单强化收藏价值"],
    keywords: ["通勤", "效率", "基础款", "衣橱整理"],
    imagePatterns: []
  }
};

export const mockCopyDraftByTopicId: Record<string, CopyDraftContent> = {
  "topic-spring-commute": {
    title: "通勤穿搭别再乱买了，4 件基础单品就够用",
    body:
      "最近天气忽冷忽热，早八通勤真的很容易穿崩。\n\n我这周把最常穿的 4 件基础单品重新整理了一遍，发现只要把颜色和版型理顺，日常上班真的不用每天想很久。\n\n如果你也想把通勤穿搭做得更省时间，这套思路可以直接照搬。"
  }
};

export const mockImageResultsByTopicId: Record<string, GeneratedImageResult[]> = {
  "topic-spring-commute": [
    {
      id: "gen-1",
      alt: "文生图封面候选图 1",
      imageUrl: createSvgCover("封面 1", "#d26f54", "#8a2d1b"),
      imagePath: "generated_images/gen-1.png",
      prompt: "生成一张通勤穿搭封面图",
      sourceEditorImageIds: ["editor-1"],
      createdAt: "2026-03-30T10:00:00+08:00",
    },
    {
      id: "gen-2",
      alt: "图生图封面候选图 1",
      imageUrl: createSvgCover("封面 2", "#b87d66", "#5f3627"),
      imagePath: "generated_images/gen-2.png",
      prompt: "参考 1 号图风格，把 2 号图主体替换进去",
      sourceEditorImageIds: ["editor-1", "editor-2"],
      createdAt: "2026-03-30T10:01:00+08:00",
    },
    {
      id: "gen-3",
      alt: "图生图内页候选图 2",
      imageUrl: createSvgCover("内页 4", "#e1c4b0", "#8b6248"),
      imagePath: "generated_images/gen-3.png",
      prompt: "生成一张同风格内页图",
      sourceEditorImageIds: ["editor-1"],
      createdAt: "2026-03-30T10:02:00+08:00",
    }
  ],
  "topic-small-rental": []
};

export const mockChatMessagesByTopicId: Record<string, ChatMessage[]> = {
  "topic-spring-commute": [
    {
      id: "message-user-collector",
      role: "user",
      text: "先围绕春季通勤穿搭去找一批高热度帖子，重点看早八、低预算、基础款这些关键词。",
      time: "10:12"
    },
    {
      id: "message-agent-collector",
      role: "agent",
      agentName: "帖子搜集 Agent",
      text: "第一轮搜集已经完成。我保留了 4 条相关度更高的候选帖子，右侧搜索结果默认展开，你可以直接点开缩略卡查看详情并决定是否加入已选。",
      time: "10:18",
      toolSummary: [
        {
          name: "xhs-explore",
          argumentsSummary: "{\"keyword\":\"春季通勤穿搭\",\"note_type\":\"图文\"}",
          resultSummary: "已返回 4 条高相关图文帖子，并完成去重。"
        }
      ]
    },
    {
      id: "message-user-summary",
      role: "user",
      text: "基于我已经选中的帖子，总结一下标题和正文结构，再给我一版完整文案。",
      time: "10:40"
    },
    {
      id: "message-agent-summary",
      role: "agent",
      agentName: "模式总结 Agent",
      text:
        "## 这批内容的共性\n\n- 标题会先切通勤场景\n- 再给出低门槛解决方案\n- 结尾常补一个清单来提高收藏意愿\n\n> 正文更强调“直接照搬”的效率感。\n\n| 维度 | 观察 |\n| --- | --- |\n| 标题 | 场景 + 解决方案 |\n| 正文 | 步骤化、可照搬 |\n\n可优先保留 `通勤场景 + 低门槛公式` 这类表达。",
      time: "10:43"
    },
    {
      id: "message-agent-copy",
      role: "agent",
      agentName: "文案创作 Agent",
      type: "copy",
      text:
        "通勤穿搭别再乱买了，4 件基础单品就够用\n\n最近天气忽冷忽热，早八通勤真的很容易穿崩。\n\n我这周把最常穿的 4 件基础单品重新整理了一遍，发现只要把颜色和版型理顺，日常上班真的不用每天想很久。\n\n如果你也想把通勤穿搭做得更省时间，这套思路可以直接照搬。",
      time: "10:58"
    }
  ],
  "topic-small-rental": []
};

export const mockConversationEntriesByTopicId: Record<string, ConversationEntry[]> = {
  "topic-spring-commute": [
    {
      id: "conversation-collector",
      time: "10:12",
      agentName: "帖子搜集 Agent",
      status: "completed",
      inputSummary: "基于春季通勤话题做检索扩写",
      outputSummary: "输出候选帖子摘要并进入人工筛选",
      detailLogs: ["打开搜索页：春季通勤穿搭", "追加检索词：早八、基础款、低预算", "抓取 4 条候选帖子并完成去重"]
    }
  ]
};
