import {
  Bot,
  CheckCircle2,
  Eye,
  EyeOff,
  Image as ImageIcon,
  KeyRound,
  RefreshCcw,
  ServerCog,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Surface } from "../components/ui/Surface";
import {
  getSettings,
  listTopics,
  testImageAnalysisSettings,
  testImageGenerationSettings,
  testLlmSettings,
  toTopicCards,
  updateImageAnalysisSettings,
  updateImageGenerationSettings,
  updateLlmSettings,
  type ProviderSettingsApiResponse,
} from "../lib/api";
import { cn } from "../lib/cn";
import type { TopicCard } from "../types/workspace";

type ProviderKey = "llm" | "imageAnalysis" | "imageGeneration";
type FeedbackTone = "success" | "error" | "neutral";

interface ProviderCardState {
  title: string;
  description: string;
  baseUrl: string;
  model: string;
  apiKeyInput: string;
  apiKeyVisible: boolean;
  apiKeyTouched: boolean;
  apiKeyConfigured: boolean;
  apiKeyMasked?: string | null;
  isSaving: boolean;
  isTesting: boolean;
  feedback?: string;
  feedbackTone?: FeedbackTone;
}

function maskApiKey(value: string): string {
  if (value.length === 0) {
    return "";
  }
  return "*".repeat(value.length);
}

function createProviderCardState(
  title: string,
  description: string,
  payload: ProviderSettingsApiResponse
): ProviderCardState {
  return {
    title,
    description,
    baseUrl: payload.base_url,
    model: payload.model,
    apiKeyInput: payload.api_key,
    apiKeyVisible: false,
    apiKeyTouched: false,
    apiKeyConfigured: payload.api_key_configured,
    apiKeyMasked: payload.api_key_masked,
    isSaving: false,
    isTesting: false,
  };
}

function toFeedbackTone(success: boolean): FeedbackTone {
  return success ? "success" : "error";
}

const PROVIDER_META: Record<
  ProviderKey,
  {
    icon: typeof Bot;
    label: string;
  }
> = {
  llm: {
    icon: Bot,
    label: "主 LLM",
  },
  imageAnalysis: {
    icon: Sparkles,
    label: "图片识别",
  },
  imageGeneration: {
    icon: ImageIcon,
    label: "图片生成",
  },
};

export function SettingsPage(): JSX.Element {
  const [topics, setTopics] = useState<TopicCard[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [cards, setCards] = useState<Record<ProviderKey, ProviderCardState> | null>(null);
  const [activeTab, setActiveTab] = useState<ProviderKey>("llm");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setPageError(null);

    void Promise.all([listTopics(), getSettings()])
      .then(([topicsResponse, settingsResponse]) => {
        if (cancelled) {
          return;
        }
        setTopics(toTopicCards(topicsResponse.items));
        setCards({
          llm: createProviderCardState(
            "主 LLM",
            "配置主对话与运行时推理所使用的 OpenAI 兼容模型。",
            settingsResponse.llm
          ),
          imageAnalysis: createProviderCardState(
            "图片识别",
            "配置图片识别 skill 所使用的多模态模型。",
            settingsResponse.image_analysis
          ),
          imageGeneration: createProviderCardState(
            "图片生成",
            "配置图片生成 skill 所使用的图像模型。",
            settingsResponse.image_generation
          ),
        });
      })
      .catch((cause: unknown) => {
        if (cancelled) {
          return;
        }
        const message = cause instanceof Error ? cause.message : "加载设置失败";
        setPageError(message);
        setTopics([]);
        setCards(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function patchCard(key: ProviderKey, updater: (current: ProviderCardState) => ProviderCardState): void {
    setCards((current) => {
      if (current === null) {
        return current;
      }
      return {
        ...current,
        [key]: updater(current[key]),
      };
    });
  }

  function applySavedPayload(key: ProviderKey, payload: ProviderSettingsApiResponse): void {
    patchCard(key, (current) => ({
      ...current,
      baseUrl: payload.base_url,
      model: payload.model,
      apiKeyInput: payload.api_key,
      apiKeyTouched: false,
      apiKeyConfigured: payload.api_key_configured,
      apiKeyMasked: payload.api_key_masked,
    }));
  }

  async function handleSave(key: ProviderKey): Promise<void> {
    if (cards === null) {
      return;
    }
    const current = cards[key];
    const payload = {
      baseUrl: current.baseUrl.trim(),
      model: current.model.trim(),
      apiKey: current.apiKeyTouched ? current.apiKeyInput : undefined,
    };

    patchCard(key, (item) => ({
      ...item,
      isSaving: true,
      feedback: undefined,
      feedbackTone: undefined,
    }));

    try {
      const response =
        key === "llm"
          ? await updateLlmSettings(payload)
          : key === "imageAnalysis"
            ? await updateImageAnalysisSettings(payload)
            : await updateImageGenerationSettings(payload);
      applySavedPayload(key, response);
      patchCard(key, (item) => ({
        ...item,
        feedback: "保存成功，后续调用将使用新配置。",
        feedbackTone: "success",
      }));
    } catch (cause: unknown) {
      const message = cause instanceof Error ? cause.message : "保存失败";
      patchCard(key, (item) => ({
        ...item,
        feedback: message,
        feedbackTone: "error",
      }));
    } finally {
      patchCard(key, (item) => ({
        ...item,
        isSaving: false,
      }));
    }
  }

  async function handleTest(key: ProviderKey): Promise<void> {
    if (cards === null) {
      return;
    }
    const current = cards[key];
    const payload = {
      baseUrl: current.baseUrl.trim(),
      model: current.model.trim(),
      apiKey: current.apiKeyTouched ? current.apiKeyInput : undefined,
    };

    patchCard(key, (item) => ({
      ...item,
      isTesting: true,
      feedback: undefined,
      feedbackTone: undefined,
    }));

    try {
      const response =
        key === "llm"
          ? await testLlmSettings(payload)
          : key === "imageAnalysis"
            ? await testImageAnalysisSettings(payload)
            : await testImageGenerationSettings(payload);
      patchCard(key, (item) => ({
        ...item,
        feedback: response.message,
        feedbackTone: toFeedbackTone(response.success),
      }));
    } catch (cause: unknown) {
      const message = cause instanceof Error ? cause.message : "连接测试失败";
      patchCard(key, (item) => ({
        ...item,
        feedback: message,
        feedbackTone: "error",
      }));
    } finally {
      patchCard(key, (item) => ({
        ...item,
        isTesting: false,
      }));
    }
  }

  const activeCard = cards ? cards[activeTab] : null;
  const activeMeta = PROVIDER_META[activeTab];

  return (
    <main
      className="grid h-screen gap-4 pr-4 pl-0"
      data-left-sidebar={isSidebarCollapsed ? "collapsed" : "open"}
      data-testid="settings-shell"
      style={{
        gridTemplateColumns: isSidebarCollapsed ? "80px minmax(0, 1fr)" : "248px minmax(0, 1fr)",
      }}
    >
      <WorkspaceSidebar
        collapsed={isSidebarCollapsed}
        currentTopicId=""
        onToggleCollapse={() => setIsSidebarCollapsed((current) => !current)}
        topics={topics}
      />

      <section className="h-screen overflow-y-auto bg-slate-50">
        <div className="scrollbar-subtle h-full overflow-y-auto px-6 py-8 sm:px-8 lg:px-10">
          <div className="mx-auto max-w-5xl">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
                <ServerCog className="h-5 w-5" strokeWidth={1.8} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-950">设置</h1>
                <p className="text-sm text-slate-500">配置你的 AI 服务</p>
              </div>
            </div>

            {pageError ? (
              <Surface className="mb-4 rounded-[20px] border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 shadow-none">
                {pageError}
              </Surface>
            ) : null}

            {isLoading ? (
              <Surface className="rounded-[20px] border border-slate-200 bg-white/90 p-6 text-sm text-slate-500 shadow-none">
                正在加载设置...
              </Surface>
            ) : null}

            {cards ? (
              <div className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
                <div
                  className="flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1"
                  data-testid="settings-tabs"
                >
                  {(Object.keys(PROVIDER_META) as ProviderKey[]).map((key) => {
                    const meta = PROVIDER_META[key];
                    const Icon = meta.icon;
                    const selected = activeTab === key;
                    return (
                      <button
                        aria-pressed={selected}
                        className={cn(
                          "inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all",
                          selected
                            ? "bg-white text-blue-600 shadow-sm"
                            : "text-slate-600 hover:text-slate-900"
                        )}
                        key={key}
                        onClick={() => setActiveTab(key)}
                        type="button"
                      >
                        <Icon className="h-4 w-4" strokeWidth={1.9} />
                        <span>{meta.label}</span>
                      </button>
                    );
                  })}
                </div>

                {activeCard ? (
                  <div className="mt-4">
                    <SettingsCard
                      card={activeCard}
                      icon={activeMeta.icon}
                      onApiKeyChange={(value) =>
                        patchCard(activeTab, (item) => ({
                          ...item,
                          apiKeyInput: value,
                          apiKeyTouched: true,
                        }))
                      }
                      onBaseUrlChange={(value) =>
                        patchCard(activeTab, (item) => ({ ...item, baseUrl: value }))
                      }
                      onClearApiKey={() =>
                        patchCard(activeTab, (item) => ({
                          ...item,
                          apiKeyInput: "",
                          apiKeyTouched: true,
                        }))
                      }
                      onToggleApiKeyVisible={() =>
                        patchCard(activeTab, (item) => ({
                          ...item,
                          apiKeyVisible: !item.apiKeyVisible,
                        }))
                      }
                      onModelChange={(value) => patchCard(activeTab, (item) => ({ ...item, model: value }))}
                      onSave={() => void handleSave(activeTab)}
                      onTest={() => void handleTest(activeTab)}
                    />
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}

function SettingsCard({
  card,
  icon: Icon,
  onBaseUrlChange,
  onApiKeyChange,
  onModelChange,
  onClearApiKey,
  onToggleApiKeyVisible,
  onSave,
  onTest,
}: {
  card: ProviderCardState;
  icon: typeof Bot;
  onBaseUrlChange: (value: string) => void;
  onApiKeyChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onClearApiKey: () => void;
  onToggleApiKeyVisible: () => void;
  onSave: () => void;
  onTest: () => void;
}): JSX.Element {
  const busy = card.isSaving || card.isTesting;
  const maskedApiKey = maskApiKey(card.apiKeyInput);
  const shouldMaskApiKey = !card.apiKeyVisible && card.apiKeyInput.length > 0;

  return (
    <Surface
      className="rounded-[20px] border border-slate-200 bg-slate-50/40 p-5 shadow-none sm:p-6"
      data-testid={`settings-card-${card.title}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-slate-600 shadow-sm ring-1 ring-slate-200">
            <Icon className="h-4.5 w-4.5" strokeWidth={1.9} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-950">{card.title}</h2>
              <Badge variant={card.apiKeyConfigured ? "success" : "neutral"}>
                {card.apiKeyConfigured ? "已配置" : "未配置"}
              </Badge>
            </div>
            <p className="mt-1.5 text-sm text-slate-500">{card.description}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="grid gap-2">
          <span className="text-sm font-medium text-slate-700">Base URL</span>
          <input
            className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-300"
            onChange={(event) => onBaseUrlChange(event.target.value)}
            value={card.baseUrl}
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-slate-700">Model</span>
          <input
            className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-300"
            onChange={(event) => onModelChange(event.target.value)}
            value={card.model}
          />
        </label>

        <label className="grid gap-2 md:col-span-2">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-medium text-slate-700">API Key</span>
            <button
              className="text-xs font-medium text-slate-500 transition-colors hover:text-slate-900"
              onClick={onClearApiKey}
              type="button"
            >
              清空 Key
            </button>
          </div>
          <div className="grid gap-2">
            <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4">
              <KeyRound className="h-4 w-4 shrink-0 text-slate-400" strokeWidth={1.8} />
              <input
                aria-label="API Key"
                className="h-11 flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
                onChange={(event) => onApiKeyChange(event.target.value)}
                placeholder={card.apiKeyConfigured ? "" : "输入 API Key"}
                readOnly={shouldMaskApiKey}
                spellCheck={false}
                type="text"
                value={shouldMaskApiKey ? maskedApiKey : card.apiKeyInput}
              />
              <button
                aria-label={card.apiKeyVisible ? "隐藏 API Key" : "显示 API Key"}
                className="shrink-0 text-slate-400 transition-colors hover:text-slate-700"
                onClick={onToggleApiKeyVisible}
                type="button"
              >
                {card.apiKeyVisible ? (
                  <EyeOff className="h-4 w-4" strokeWidth={1.8} />
                ) : (
                  <Eye className="h-4 w-4" strokeWidth={1.8} />
                )}
              </button>
            </div>
          </div>
        </label>
      </div>

      <div className="mt-5 flex flex-col gap-4 pt-1 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-h-6 flex-1">
          {card.feedback ? (
            <p
              className={cn(
                "flex items-center gap-1.5 text-sm",
                card.feedbackTone === "success"
                  ? "text-emerald-700"
                  : card.feedbackTone === "error"
                    ? "text-rose-700"
                    : "text-slate-500"
              )}
            >
              {card.feedbackTone === "success" ? <CheckCircle2 className="h-4 w-4" strokeWidth={1.8} /> : null}
              <span>{card.feedback}</span>
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button className="min-w-[88px]" disabled={busy} onClick={onTest} type="button" variant="secondary">
            {card.isTesting ? (
              <>
                <RefreshCcw className="h-4 w-4 animate-spin" strokeWidth={1.8} />
                测试中
              </>
            ) : (
              "测试"
            )}
          </Button>
          <Button className="min-w-[88px]" disabled={busy} onClick={onSave} type="button" variant="primary">
            {card.isSaving ? "保存中" : "保存"}
          </Button>
        </div>
      </div>
    </Surface>
  );
}
