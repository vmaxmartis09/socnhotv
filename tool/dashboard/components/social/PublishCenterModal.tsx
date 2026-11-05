"use client";

import React, { useEffect, useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import {
  socialApi,
  PublishableVideo,
  PlannedTarget,
  PlatformCaptionResult,
  PlatformType,
  SocialAccount,
  TargetCommitSpec,
} from "@/lib/api/social";
import { PhonePreview } from "./PhonePreview";
import { CalendarView } from "./CalendarView";
import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  Layers,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Tag,
  Trash2,
  Video,
  X,
} from "./icons";

interface PublishCenterModalProps {
  projectId: string;
  isOpen: boolean;
  initialTab?: "plan" | "calendar";
  initialVideoIds?: string[];
  onClose: () => void;
}

export function PublishCenterModal({
  projectId,
  isOpen,
  initialTab = "plan",
  initialVideoIds,
  onClose,
}: PublishCenterModalProps) {
  const { accounts, loadAccounts, loadQueue, loadAll } = useSocialStore();

  const [activeMainTab, setActiveMainTab] = useState<"plan" | "calendar">(initialTab);
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: Videos
  const [videos, setVideos] = useState<PublishableVideo[]>([]);
  const [loadingVideos, setLoadingVideos] = useState<boolean>(false);
  const [videoSearch, setVideoSearch] = useState("");
  const [filterUnpostedOnly, setFilterUnpostedOnly] = useState(false);
  const [selectedVideoIds, setSelectedVideoIds] = useState<string[]>([]);

  // Pre-select videos if passed from Social Hub
  useEffect(() => {
    if (isOpen && initialVideoIds && initialVideoIds.length > 0) {
      setSelectedVideoIds(initialVideoIds);
      setCurrentStep(2); // Jump directly to Step 2 (Account selection)
    }
  }, [isOpen, initialVideoIds]);

  // Step 2: Accounts & Matrix
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [selectedGroupFilter, setSelectedGroupFilter] = useState<string>("all");
  const [ignoreErrors, setIgnoreErrors] = useState<boolean>(false);

  // Step 3: Content & Captions
  const [activeVideoIndex, setActiveVideoIndex] = useState<number>(0);
  const [activePlatformTab, setActivePlatformTab] = useState<string>("all");
  const [videoCaptions, setVideoCaptions] = useState<
    Record<
      string, // videoId
      {
        mainCaption: string;
        tone: string;
        goal: string;
        includeAffiliate: boolean;
        affiliateLink: string;
        varyPerAccount: boolean;
        platformData: Record<
          string, // platform or accountId
          {
            title?: string;
            caption: string;
            hashtags: string[];
            privacy: string;
            madeForKids: boolean;
            aiGeneratedLabel: boolean;
            firstComment: string;
          }
        >;
      }
    >
  >({});
  const [isGeneratingCaptions, setIsGeneratingCaptions] = useState<boolean>(false);

  // Step 4: Schedule
  const [scheduleStrategy, setScheduleStrategy] = useState<"auto" | "now" | "fixed">("auto");
  const [scheduleStartDate, setScheduleStartDate] = useState<string>(() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() + 15);
    return d.toISOString().slice(0, 16);
  });
  const [perDayLimit, setPerDayLimit] = useState<number>(3);
  const [previewTargets, setPreviewTargets] = useState<PlannedTarget[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState<boolean>(false);

  // Step 5: Commit
  const [approvalRequired, setApprovalRequired] = useState<boolean>(true);
  const [isSubmittingPlan, setIsSubmittingPlan] = useState<boolean>(false);
  const [commitResult, setCommitResult] = useState<{
    postsCount: number;
    targetsCount: number;
  } | null>(null);

  // Load videos and accounts when modal opens
  useEffect(() => {
    if (isOpen && projectId) {
      setLoadingVideos(true);
      socialApi
        .getVideos(projectId)
        .then((vids) => {
          setVideos(vids);
          if (vids.length > 0 && selectedVideoIds.length === 0) {
            setSelectedVideoIds([vids[0].id]);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingVideos(false));

      if (accounts.length === 0) {
        loadAccounts(projectId);
      }
    }
  }, [isOpen, projectId, loadAccounts]);

  // Select all accounts by default if empty
  useEffect(() => {
    if (accounts.length > 0 && selectedAccountIds.length === 0) {
      setSelectedAccountIds(accounts.map((a) => a.id));
    }
  }, [accounts, selectedAccountIds.length]);

  // Groups list from accounts
  const allGroups = useMemo(() => {
    const set = new Set<string>();
    accounts.forEach((a) => {
      (a.groups || []).forEach((g) => set.add(g));
    });
    return Array.from(set);
  }, [accounts]);

  // Filtered videos
  const filteredVideos = useMemo(() => {
    return videos.filter((v) => {
      const matchSearch =
        !videoSearch || v.title.toLowerCase().includes(videoSearch.toLowerCase());
      const matchUnposted = !filterUnpostedOnly || v.posted_count === 0;
      return matchSearch && matchUnposted;
    });
  }, [videos, videoSearch, filterUnpostedOnly]);

  const selectedVideos = useMemo(() => {
    return videos.filter((v) => selectedVideoIds.includes(v.id));
  }, [videos, selectedVideoIds]);

  const selectedAccounts = useMemo(() => {
    return accounts.filter((a) => selectedAccountIds.includes(a.id));
  }, [accounts, selectedAccountIds]);

  // Compatibility evaluation for Step 2 Matrix
  const compatibilityMatrix = useMemo(() => {
    const matrix: Record<string, Record<string, { status: "ok" | "warn" | "error"; message?: string }>> = {};
    for (const v of selectedVideos) {
      matrix[v.id] = {};
      for (const a of selectedAccounts) {
        if (a.status === "expired") {
          matrix[v.id][a.id] = { status: "error", message: `Tài khoản ${a.display_name} đã hết hạn OAuth` };
          continue;
        }
        if (a.platform === "tiktok" && v.duration_s > 600) {
          matrix[v.id][a.id] = { status: "error", message: "Video dài hơn 600s của TikTok" };
          continue;
        }
        if (a.platform === "tiktok" && v.aspect_ratio === "16:9" && !v.variants["tiktok"] && !v.variants["shorts"]) {
          matrix[v.id][a.id] = { status: "warn", message: "Video 16:9 ngang; TikTok khuyên dùng dọc 9:16" };
          continue;
        }
        matrix[v.id][a.id] = { status: "ok", message: "Tương thích hoàn hảo" };
      }
    }
    return matrix;
  }, [selectedVideos, selectedAccounts]);

  // Handle Generate Captions AI in Step 3
  const handleGenerateCaptions = async (forAllVideos = false) => {
    setIsGeneratingCaptions(true);
    try {
      const vidsToProcess = forAllVideos ? selectedVideos : [selectedVideos[activeVideoIndex]];
      const targetPlatforms = Array.from(new Set(selectedAccounts.map((a) => a.platform)));

      for (const v of vidsToProcess) {
        if (!v) continue;
        const currentData = videoCaptions[v.id] || {
          mainCaption: "",
          tone: "friendly",
          goal: "story",
          includeAffiliate: false,
          affiliateLink: "",
          varyPerAccount: false,
          platformData: {},
        };

        const res = await socialApi.generateCaptions(projectId, {
          video_id: v.id,
          platforms: targetPlatforms,
          tone: currentData.tone,
          goal: currentData.goal,
          include_affiliate: currentData.includeAffiliate,
          affiliate_link: currentData.affiliateLink,
          vary_per_account: currentData.varyPerAccount,
          account_ids: selectedAccountIds,
        });

        const newPlatformData: Record<string, any> = { ...currentData.platformData };
        let firstCaption = "";
        res.forEach((r) => {
          if (!firstCaption) firstCaption = r.caption;
          const key = r.account_id || r.platform;
          newPlatformData[key] = {
            title: r.title || v.title,
            caption: r.caption,
            hashtags: r.hashtags,
            privacy: "public",
            madeForKids: false,
            aiGeneratedLabel: false,
            firstComment: "",
          };
        });

        setVideoCaptions((prev) => ({
          ...prev,
          [v.id]: {
            ...currentData,
            mainCaption: firstCaption || currentData.mainCaption,
            platformData: newPlatformData,
          },
        }));
      }
    } catch (err: any) {
      alert(`Lỗi sinh caption: ${err.message}`);
    } finally {
      setIsGeneratingCaptions(false);
    }
  };

  // Handle Preview Plan in Step 4
  const handleLoadPreview = async () => {
    if (selectedVideoIds.length === 0 || selectedAccountIds.length === 0) return;
    setIsLoadingPreview(true);
    try {
      const planned = await socialApi.previewPlan(projectId, {
        video_ids: selectedVideoIds,
        account_ids: selectedAccountIds,
        strategy: scheduleStrategy,
        start_at: new Date(scheduleStartDate).toISOString(),
        per_day_limit: perDayLimit,
      });
      setPreviewTargets(planned);
    } catch (err: any) {
      alert(`Lỗi xem trước lịch: ${err.message}`);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  useEffect(() => {
    if (currentStep === 4) {
      handleLoadPreview();
    }
  }, [currentStep, scheduleStrategy, perDayLimit]);

  // Handle Commit in Step 5
  const handleCommitPlan = async () => {
    setIsSubmittingPlan(true);
    try {
      const commitSpecs: TargetCommitSpec[] = previewTargets.map((pt) => {
        const vCap = videoCaptions[pt.video_id];
        const pData = vCap?.platformData?.[pt.account_id] || vCap?.platformData?.[pt.platform];

        return {
          video_id: pt.video_id,
          account_id: pt.account_id,
          scheduled_at: pt.scheduled_at,
          title: pData?.title || pt.video_title,
          caption: pData?.caption || vCap?.mainCaption || pt.video_title,
          hashtags: pData?.hashtags || [],
          privacy: pData?.privacy || "public",
          made_for_kids: pData?.madeForKids || false,
          ai_generated_label: pData?.aiGeneratedLabel || false,
          firstComment: pData?.firstComment || "",
          product_link: vCap?.affiliateLink || "",
          disclosure_ad: vCap?.includeAffiliate || false,
        };
      });

      const res = await socialApi.commitPlan(projectId, commitSpecs, approvalRequired);
      setCommitResult({
        postsCount: res.created_posts_count,
        targetsCount: res.created_targets_count,
      });
      await loadAll(projectId);
    } catch (err: any) {
      alert(`Lỗi lưu lịch xuất bản: ${err.message}`);
    } finally {
      setIsSubmittingPlan(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-3 sm:p-6 animate-in fade-in-50">
      <div className="relative w-full max-w-6xl h-[92vh] flex flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden text-foreground">
        {/* Top Modal Header */}
        <div className="flex items-center justify-between border-b border-border bg-muted/40 px-5 py-3.5 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <CalendarDays className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-foreground flex items-center gap-2">
                Trung tâm Quản lý & Xuất bản Social
                <span className="text-[11px] font-normal text-muted-foreground bg-accent px-2 py-0.5 rounded-full border border-border">
                  {accounts.length}/10 tài khoản
                </span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Lập kế hoạch xuất bản đa kênh, tối ưu caption và kiểm soát an toàn trước khi đăng
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Tab switchers: Wizard Plan vs Calendar */}
            <div className="flex items-center rounded-xl border border-border bg-background p-1 text-xs">
              <button
                type="button"
                onClick={() => setActiveMainTab("plan")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1 font-semibold transition-all",
                  activeMainTab === "plan"
                    ? "bg-primary text-primary-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Kế hoạch đăng (5 bước)</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveMainTab("calendar")}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1 font-semibold transition-all",
                  activeMainTab === "calendar"
                    ? "bg-primary text-primary-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Calendar className="h-3.5 w-3.5" />
                <span>Xem Lịch Đăng</span>
              </button>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Modal Main Body */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {activeMainTab === "calendar" ? (
            /* Tab 2: Calendar View */
            <div className="flex-1 p-4 overflow-y-auto">
              <CalendarView projectId={projectId} />
            </div>
          ) : (
            /* Tab 1: 5-Step Plan Wizard */
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Stepper Header */}
              <div className="flex items-center justify-between border-b border-border bg-background px-6 py-2.5 text-xs">
                {[
                  { step: 1, title: "1. Chọn video", icon: Video },
                  { step: 2, title: "2. Chọn kênh & Tương thích", icon: Layers },
                  { step: 3, title: "3. Nội dung & Xem trước", icon: Smartphone },
                  { step: 4, title: "4. Lập lịch tự động", icon: Clock },
                  { step: 5, title: "5. Duyệt & Xác nhận", icon: ShieldCheck },
                ].map((s) => {
                  const Icon = s.icon;
                  const isCurrent = currentStep === s.step;
                  const isDone = currentStep > s.step;
                  return (
                    <button
                      key={s.step}
                      type="button"
                      onClick={() => setCurrentStep(s.step)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all",
                        isCurrent
                          ? "bg-primary/10 text-primary border border-primary/20 shadow-2xs"
                          : isDone
                          ? "text-emerald-500 hover:bg-emerald-500/10"
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold",
                          isCurrent
                            ? "bg-primary text-primary-foreground"
                            : isDone
                            ? "bg-emerald-500 text-white"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {isDone ? "✓" : s.step}
                      </span>
                      <span className="hidden md:inline">{s.title}</span>
                    </button>
                  );
                })}
              </div>

              {/* Step Content Container */}
              <div className="flex-1 overflow-y-auto p-5">
                {/* STEP 1: Select Video */}
                {currentStep === 1 && (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="relative flex-1 min-w-[240px]">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                          type="text"
                          value={videoSearch}
                          onChange={(e) => setVideoSearch(e.target.value)}
                          placeholder="Tìm kiếm video theo tiêu đề..."
                          className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={filterUnpostedOnly}
                            onChange={(e) => setFilterUnpostedOnly(e.target.checked)}
                            className="rounded border-border text-primary focus:ring-primary"
                          />
                          <span>Chỉ hiện video chưa đăng</span>
                        </label>
                        <span className="rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                          Đã chọn {selectedVideoIds.length} video
                        </span>
                      </div>
                    </div>

                    {loadingVideos ? (
                      <div className="py-20 text-center text-xs text-muted-foreground">
                        Đang quét kho video hoàn tất...
                      </div>
                    ) : filteredVideos.length === 0 ? (
                      <div className="py-16 text-center text-xs text-muted-foreground border-2 border-dashed border-border rounded-xl">
                        Không tìm thấy video nào phù hợp. Hãy render thêm video tại Studio.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {filteredVideos.map((v) => {
                          const isSelected = selectedVideoIds.includes(v.id);
                          return (
                            <div
                              key={v.id}
                              onClick={() => {
                                if (isSelected) {
                                  setSelectedVideoIds(selectedVideoIds.filter((id) => id !== v.id));
                                } else {
                                  setSelectedVideoIds([...selectedVideoIds, v.id]);
                                }
                              }}
                              className={cn(
                                "group relative flex flex-col rounded-xl border bg-card overflow-hidden cursor-pointer transition-all shadow-2xs hover:border-primary/60",
                                isSelected
                                  ? "border-primary ring-2 ring-primary/20 bg-primary/5"
                                  : "border-border"
                              )}
                            >
                              <div className="relative aspect-video w-full bg-muted flex items-center justify-center overflow-hidden">
                                {v.thumb ? (
                                  <img
                                    src={`/api/media?path=${encodeURIComponent(v.thumb)}`}
                                    alt={v.title}
                                    className="h-full w-full object-cover"
                                  />
                                ) : (
                                  <Video className="h-8 w-8 text-muted-foreground/50" />
                                )}
                                <div className="absolute top-2 left-2 rounded-md bg-black/60 backdrop-blur-md px-1.5 py-0.5 text-[10px] font-mono font-bold text-white">
                                  {v.aspect_ratio} · {v.duration_s.toFixed(0)}s
                                </div>
                                <div className="absolute top-2 right-2">
                                  <div
                                    className={cn(
                                      "h-5 w-5 rounded-md border flex items-center justify-center transition-colors",
                                      isSelected
                                        ? "bg-primary border-primary text-primary-foreground"
                                        : "bg-black/40 border-white/40 text-transparent"
                                    )}
                                  >
                                    ✓
                                  </div>
                                </div>
                              </div>
                              <div className="p-3 space-y-1.5 flex-1 flex flex-col justify-between">
                                <p className="text-xs font-semibold text-foreground line-clamp-2" title={v.title}>
                                  {v.title}
                                </p>
                                <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/50">
                                  <span>{v.size_mb} MB</span>
                                  <span
                                    className={cn(
                                      "font-medium",
                                      v.posted_count > 0 ? "text-amber-500" : "text-emerald-500"
                                    )}
                                  >
                                    {v.posted_count > 0 ? `Đã đăng ${v.posted_count} lần` : "Chưa đăng"}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* STEP 2: Select Accounts & Matrix */}
                {currentStep === 2 && (
                  <div className="space-y-5">
                    {/* Account selection header */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                          Chọn tài khoản ({selectedAccountIds.length}/{accounts.length}):
                        </span>
                        {allGroups.map((g) => (
                          <button
                            key={g}
                            type="button"
                            onClick={() => {
                              const groupAccIds = accounts
                                .filter((a) => (a.groups || []).includes(g))
                                .map((a) => a.id);
                              setSelectedAccountIds(Array.from(new Set([...selectedAccountIds, ...groupAccIds])));
                            }}
                            className="rounded-lg border border-border bg-accent px-2 py-0.5 text-[11px] font-medium text-foreground hover:bg-accent/80 transition-colors"
                          >
                            + Nhóm "{g}"
                          </button>
                        ))}
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedAccountIds(accounts.map((a) => a.id))}
                          className="text-xs text-primary hover:underline font-semibold"
                        >
                          Chọn tất cả ({accounts.length})
                        </button>
                        <span className="text-muted-foreground">·</span>
                        <button
                          type="button"
                          onClick={() => setSelectedAccountIds([])}
                          className="text-xs text-muted-foreground hover:underline"
                        >
                          Bỏ chọn tất cả
                        </button>
                      </div>
                    </div>

                    {/* Accounts selection row */}
                    <div className="flex flex-wrap gap-2">
                      {accounts.map((acc) => {
                        const isSelected = selectedAccountIds.includes(acc.id);
                        return (
                          <div
                            key={acc.id}
                            onClick={() => {
                              if (isSelected) {
                                setSelectedAccountIds(selectedAccountIds.filter((id) => id !== acc.id));
                              } else {
                                if (selectedAccountIds.length >= 10) {
                                  alert("Tối đa chọn 10 tài khoản");
                                  return;
                                }
                                setSelectedAccountIds([...selectedAccountIds, acc.id]);
                              }
                            }}
                            className={cn(
                              "flex items-center gap-2 rounded-xl border p-2 cursor-pointer transition-all select-none shadow-2xs",
                              isSelected
                                ? "border-primary bg-primary/10 text-foreground"
                                : "border-border bg-card text-muted-foreground hover:border-primary/40"
                            )}
                          >
                            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent text-[10px] font-bold uppercase text-foreground">
                              {acc.platform.slice(0, 2)}
                            </div>
                            <div className="text-left">
                              <p className="text-xs font-semibold leading-none text-foreground">{acc.display_name}</p>
                              <p className="text-[10px] text-muted-foreground">{acc.platform}</p>
                            </div>
                            <div
                              className={cn(
                                "ml-1 h-4 w-4 rounded-full border flex items-center justify-center text-[10px]",
                                isSelected ? "bg-primary border-primary text-white" : "border-muted-foreground/40"
                              )}
                            >
                              {isSelected ? "✓" : ""}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Compatibility Matrix: Video x Account */}
                    <div className="space-y-2 pt-2 border-t border-border">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-foreground flex items-center gap-2">
                          <Layers className="h-4 w-4 text-primary" />
                          Ma trận Tương thích ({selectedVideos.length} Video × {selectedAccounts.length} Tài khoản)
                        </h4>
                        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                          <input
                            type="checkbox"
                            checked={ignoreErrors}
                            onChange={(e) => setIgnoreErrors(e.target.checked)}
                            className="rounded border-border text-primary focus:ring-primary"
                          />
                          <span>Bỏ qua các cặp cảnh báo / lỗi khi lên lịch</span>
                        </label>
                      </div>

                      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-2xs">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-muted/50 border-b border-border text-[11px] font-semibold text-muted-foreground">
                            <tr>
                              <th className="p-3 font-medium">Video đã chọn</th>
                              {selectedAccounts.map((acc) => (
                                <th key={acc.id} className="p-3 text-center min-w-[120px]">
                                  <div className="flex flex-col items-center">
                                    <span className="font-bold text-foreground">{acc.display_name}</span>
                                    <span className="text-[10px] uppercase font-normal">{acc.platform}</span>
                                  </div>
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border/60">
                            {selectedVideos.map((v) => (
                              <tr key={v.id} className="hover:bg-accent/20 transition-colors">
                                <td className="p-3 max-w-[240px]">
                                  <p className="font-semibold text-foreground truncate">{v.title}</p>
                                  <p className="text-[10px] text-muted-foreground font-mono">
                                    {v.aspect_ratio} · {v.duration_s.toFixed(0)}s · {v.size_mb}MB
                                  </p>
                                </td>
                                {selectedAccounts.map((acc) => {
                                  const cell = compatibilityMatrix[v.id]?.[acc.id] || { status: "ok" };
                                  return (
                                    <td key={acc.id} className="p-3 text-center">
                                      {cell.status === "ok" && (
                                        <span
                                          title={cell.message}
                                          className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-emerald-500/10 text-emerald-500 font-bold border border-emerald-500/20"
                                        >
                                          ✓
                                        </span>
                                      )}
                                      {cell.status === "warn" && (
                                        <span
                                          title={cell.message}
                                          className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-amber-500/10 text-amber-500 font-bold border border-amber-500/20"
                                        >
                                          ⚠
                                        </span>
                                      )}
                                      {cell.status === "error" && (
                                        <span
                                          title={cell.message}
                                          className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-rose-500/10 text-rose-500 font-bold border border-rose-500/20"
                                        >
                                          ✕
                                        </span>
                                      )}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {/* STEP 3: Content & Phone Preview */}
                {currentStep === 3 && (
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                    {/* Left side: Content Editor (7 cols) */}
                    <div className="lg:col-span-7 space-y-4">
                      {/* Video selector switcher if multiple */}
                      {selectedVideos.length > 1 && (
                        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                          {selectedVideos.map((v, idx) => (
                            <button
                              key={v.id}
                              type="button"
                              onClick={() => setActiveVideoIndex(idx)}
                              className={cn(
                                "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold whitespace-nowrap transition-colors border",
                                activeVideoIndex === idx
                                  ? "bg-primary text-primary-foreground border-primary"
                                  : "bg-muted text-muted-foreground border-border hover:bg-accent"
                              )}
                            >
                              <span>Video {idx + 1}</span>
                              <span className="truncate max-w-[120px] font-normal">{v.title}</span>
                            </button>
                          ))}
                        </div>
                      )}

                      {/* AI Generator Bar */}
                      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-primary/20 bg-primary/5 p-3">
                        <div className="flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-primary" />
                          <span className="text-xs font-bold text-foreground">Trợ lý Kịch bản AI:</span>
                          <select
                            value={videoCaptions[selectedVideos[activeVideoIndex]?.id]?.goal || "story"}
                            onChange={(e) => {
                              const curVidId = selectedVideos[activeVideoIndex]?.id;
                              if (!curVidId) return;
                              setVideoCaptions((prev) => ({
                                ...prev,
                                [curVidId]: { ...(prev[curVidId] || {}), goal: e.target.value } as any,
                              }));
                            }}
                            className="rounded-lg border border-border bg-background px-2 py-1 text-xs text-foreground"
                          >
                            <option value="story">Kể chuyện / Giải trí</option>
                            <option value="education">Giáo dục / Kiến thức</option>
                            <option value="sales">Bán hàng / KOC Affiliate</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-2">
                          <label className="flex items-center gap-1 text-[11px] text-muted-foreground cursor-pointer">
                            <input
                              type="checkbox"
                              checked={videoCaptions[selectedVideos[activeVideoIndex]?.id]?.varyPerAccount || false}
                              onChange={(e) => {
                                const curVidId = selectedVideos[activeVideoIndex]?.id;
                                if (!curVidId) return;
                                setVideoCaptions((prev) => ({
                                  ...prev,
                                  [curVidId]: { ...(prev[curVidId] || {}), varyPerAccount: e.target.checked } as any,
                                }));
                              }}
                              className="rounded border-border text-primary"
                            />
                            <span>Mỗi tài khoản một biến thể</span>
                          </label>

                          <button
                            type="button"
                            disabled={isGeneratingCaptions}
                            onClick={() => handleGenerateCaptions(false)}
                            className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-2xs disabled:opacity-50"
                          >
                            <Sparkles className="h-3 w-3" />
                            <span>{isGeneratingCaptions ? "Đang viết..." : "Viết caption tự động"}</span>
                          </button>
                        </div>
                      </div>

                      {/* Main Caption Textarea */}
                      {(() => {
                        const curVid = selectedVideos[activeVideoIndex];
                        if (!curVid) return null;
                        const capData = videoCaptions[curVid.id] || {
                          mainCaption: curVid.title,
                          includeAffiliate: false,
                          affiliateLink: "",
                          platformData: {},
                        };

                        return (
                          <div className="space-y-3 rounded-xl border border-border bg-card p-4 shadow-2xs">
                            <div className="flex items-center justify-between">
                              <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                                <Tag className="h-3.5 w-3.5 text-primary" />
                                Caption chính:
                              </label>
                              <span className="text-[11px] font-mono text-muted-foreground">
                                {capData.mainCaption?.length || 0} ký tự
                              </span>
                            </div>

                            <textarea
                              rows={4}
                              value={capData.mainCaption}
                              onChange={(e) => {
                                setVideoCaptions((prev) => ({
                                  ...prev,
                                  [curVid.id]: { ...capData, mainCaption: e.target.value },
                                }));
                              }}
                              placeholder="Nhập nội dung caption bài viết..."
                              className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed"
                            />

                            {/* Affiliate link input */}
                            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border">
                              <label className="flex items-center gap-2 text-xs text-foreground cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={capData.includeAffiliate}
                                  onChange={(e) => {
                                    setVideoCaptions((prev) => ({
                                      ...prev,
                                      [curVid.id]: { ...capData, includeAffiliate: e.target.checked },
                                    }));
                                  }}
                                  className="rounded border-border text-primary"
                                />
                                <span className="font-medium">Chèn liên kết tiếp thị liên kết (Affiliate / KOC)</span>
                              </label>

                              {capData.includeAffiliate && (
                                <input
                                  type="text"
                                  value={capData.affiliateLink}
                                  onChange={(e) => {
                                    setVideoCaptions((prev) => ({
                                      ...prev,
                                      [curVid.id]: { ...capData, affiliateLink: e.target.value },
                                    }));
                                  }}
                                  placeholder="https://shopee.vn/..."
                                  className="flex-1 min-w-[200px] rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground"
                                />
                              )}
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Right side: Phone Preview (5 cols) */}
                    <div className="lg:col-span-5 flex flex-col items-center justify-center p-2 rounded-2xl border border-border bg-muted/20">
                      {(() => {
                        const curVid = selectedVideos[activeVideoIndex];
                        const capData = curVid ? videoCaptions[curVid.id] : null;
                        const firstAcc = selectedAccounts[0];

                        return (
                          <PhonePreview
                            platform={firstAcc ? firstAcc.platform : "tiktok"}
                            title={curVid?.title || "Sóc Nhỏ TV"}
                            caption={capData?.mainCaption || curVid?.title || ""}
                            accountHandle={firstAcc ? firstAcc.handle : "@socnhotv.official"}
                            videoThumb={curVid?.thumb}
                            productLink={capData?.includeAffiliate ? capData?.affiliateLink : undefined}
                          />
                        );
                      })()}
                    </div>
                  </div>
                )}

                {/* STEP 4: Auto-Schedule Plan */}
                {currentStep === 4 && (
                  <div className="space-y-4">
                    {/* Strategy and filters bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-2xs">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-foreground">Chiến lược lên lịch:</span>
                        <div className="flex items-center rounded-lg border border-border bg-background p-0.5 text-xs">
                          <button
                            type="button"
                            onClick={() => setScheduleStrategy("auto")}
                            className={cn(
                              "rounded-md px-2.5 py-1 font-semibold transition-all",
                              scheduleStrategy === "auto"
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:text-foreground"
                            )}
                          >
                            Tự xếp lịch chuẩn (Auto)
                          </button>
                          <button
                            type="button"
                            onClick={() => setScheduleStrategy("now")}
                            className={cn(
                              "rounded-md px-2.5 py-1 font-semibold transition-all",
                              scheduleStrategy === "now"
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:text-foreground"
                            )}
                          >
                            Đăng ngay
                          </button>
                          <button
                            type="button"
                            onClick={() => setScheduleStrategy("fixed")}
                            className={cn(
                              "rounded-md px-2.5 py-1 font-semibold transition-all",
                              scheduleStrategy === "fixed"
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:text-foreground"
                            )}
                          >
                            Giờ cố định
                          </button>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <label className="flex items-center gap-1.5 text-muted-foreground">
                          <span>Bắt đầu từ:</span>
                          <input
                            type="datetime-local"
                            value={scheduleStartDate}
                            onChange={(e) => setScheduleStartDate(e.target.value)}
                            className="rounded-lg border border-border bg-background px-2 py-1 text-xs text-foreground font-mono"
                          />
                        </label>

                        <button
                          type="button"
                          onClick={handleLoadPreview}
                          className="flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-accent transition-colors shadow-2xs"
                        >
                          <RefreshCw className="h-3 w-3" />
                          <span>Xếp lại</span>
                        </button>
                      </div>
                    </div>

                    {/* Preview Table */}
                    {isLoadingPreview ? (
                      <div className="py-20 text-center text-xs text-muted-foreground">
                        Đang phân tích khung giờ vàng và tính toán hạn ngạch quota...
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Tổng cộng: {previewTargets.length} mục tiêu xuất bản</span>
                          <span className="font-mono text-[11px]">Múi giờ: Asia/Ho_Chi_Minh (+07:00)</span>
                        </div>

                        <div className="rounded-xl border border-border bg-card overflow-hidden shadow-2xs">
                          <table className="w-full text-xs text-left">
                            <thead className="bg-muted/50 border-b border-border text-[11px] font-semibold text-muted-foreground">
                              <tr>
                                <th className="p-3">Video</th>
                                <th className="p-3">Kênh xuất bản</th>
                                <th className="p-3">Thời gian lên lịch</th>
                                <th className="p-3">Biến thể video</th>
                                <th className="p-3 text-right">Trạng thái / Cảnh báo</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border/60">
                              {previewTargets.map((pt, idx) => (
                                <tr key={`${pt.video_id}_${pt.account_id}_${idx}`} className="hover:bg-accent/20">
                                  <td className="p-3 font-semibold text-foreground max-w-[200px] truncate">
                                    {pt.video_title}
                                  </td>
                                  <td className="p-3">
                                    <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
                                      <span className="h-2 w-2 rounded-full bg-primary" />
                                      {pt.account_name} ({pt.platform})
                                    </span>
                                  </td>
                                  <td className="p-3 font-mono font-medium text-foreground">
                                    <input
                                      type="datetime-local"
                                      value={pt.scheduled_at.slice(0, 16)}
                                      onChange={(e) => {
                                        const newTime = e.target.value;
                                        setPreviewTargets((prev) =>
                                          prev.map((item, i) =>
                                            i === idx ? { ...item, scheduled_at: `${newTime}:00+07:00` } : item
                                          )
                                        );
                                      }}
                                      className="rounded-md border border-border bg-background px-2 py-0.5 text-xs text-foreground font-mono"
                                    />
                                  </td>
                                  <td className="p-3 text-muted-foreground font-mono">
                                    {pt.variant_used || "Mặc định"}
                                  </td>
                                  <td className="p-3 text-right">
                                    {pt.issues && pt.issues.length > 0 ? (
                                      <span
                                        title={pt.issues.map((i) => i.message_vi).join("\n")}
                                        className="inline-flex items-center gap-1 text-amber-500 font-medium"
                                      >
                                        <AlertTriangle className="h-3 w-3" />
                                        <span>{pt.issues[0].code}</span>
                                      </span>
                                    ) : (
                                      <span className="text-emerald-500 font-medium">✓ Sẵn sàng</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* STEP 5: Confirm & Commit */}
                {currentStep === 5 && (
                  <div className="space-y-5 max-w-2xl mx-auto py-4">
                    {commitResult ? (
                      /* Success Screen */
                      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-8 text-center space-y-4">
                        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500 mx-auto">
                          <CheckCircle2 className="h-8 w-8" />
                        </div>
                        <h3 className="text-lg font-bold text-foreground">Lên kế hoạch xuất bản thành công!</h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Đã tạo thành công <strong>{commitResult.postsCount} bài viết</strong> với{" "}
                          <strong>{commitResult.targetsCount} mục tiêu xuất bản</strong>. Các bài viết đã được đưa vào
                          hàng đợi và sẽ xuất bản đúng khung giờ đã lên lịch.
                        </p>
                        <div className="flex items-center justify-center gap-3 pt-2">
                          <button
                            type="button"
                            onClick={() => setActiveMainTab("calendar")}
                            className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow"
                          >
                            Xem trên Lịch Đăng
                          </button>
                          <button
                            type="button"
                            onClick={onClose}
                            className="rounded-xl border border-border bg-background px-4 py-2 text-xs font-semibold text-foreground hover:bg-accent transition-colors shadow-2xs"
                          >
                            Đóng cửa sổ
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* Review and Commit Table */
                      <div className="space-y-5">
                        <div className="rounded-xl border border-border bg-card p-4 space-y-3 shadow-2xs">
                          <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                            Tóm tắt kế hoạch xuất bản:
                          </h4>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                            <div className="rounded-lg bg-muted p-2.5">
                              <p className="text-[11px] text-muted-foreground">Video đã chọn</p>
                              <p className="text-base font-bold text-foreground">{selectedVideos.length}</p>
                            </div>
                            <div className="rounded-lg bg-muted p-2.5">
                              <p className="text-[11px] text-muted-foreground">Tài khoản</p>
                              <p className="text-base font-bold text-foreground">{selectedAccounts.length}</p>
                            </div>
                            <div className="rounded-lg bg-muted p-2.5">
                              <p className="text-[11px] text-muted-foreground">Tổng lượt đăng</p>
                              <p className="text-base font-bold text-primary">{previewTargets.length}</p>
                            </div>
                            <div className="rounded-lg bg-muted p-2.5">
                              <p className="text-[11px] text-muted-foreground">Khung giờ</p>
                              <p className="text-base font-bold text-foreground">
                                {scheduleStrategy === "now" ? "Đăng ngay" : "Tự động"}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Safe lock toggle */}
                        <div className="flex items-center justify-between rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                          <div className="space-y-0.5">
                            <p className="text-xs font-bold text-amber-500 flex items-center gap-1.5">
                              <ShieldCheck className="h-4 w-4" />
                              Duyệt trước khi đăng (Khóa an toàn)
                            </p>
                            <p className="text-[11px] text-muted-foreground">
                              Mọi bài viết sẽ dừng ở hàng chờ duyệt để bạn kiểm tra trước khi tự động xuất bản
                            </p>
                          </div>
                          <input
                            type="checkbox"
                            checked={approvalRequired}
                            onChange={(e) => setApprovalRequired(e.target.checked)}
                            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                          />
                        </div>

                        {/* Action Commit Button */}
                        <button
                          type="button"
                          disabled={isSubmittingPlan || previewTargets.length === 0}
                          onClick={handleCommitPlan}
                          className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary py-3 text-xs font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg disabled:opacity-50"
                        >
                          <Check className="h-4 w-4" />
                          <span>{isSubmittingPlan ? "Đang lên lịch..." : "Xác nhận lên lịch tất cả bài viết"}</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Wizard Bottom Navigation Bar */}
              <div className="flex items-center justify-between border-t border-border bg-background px-6 py-3 shrink-0 text-xs">
                <button
                  type="button"
                  disabled={currentStep === 1}
                  onClick={() => setCurrentStep(currentStep - 1)}
                  className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 py-1.5 font-semibold text-foreground hover:bg-accent transition-colors disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>Quay lại</span>
                </button>

                <div className="text-muted-foreground font-mono">Bước {currentStep} / 5</div>

                {currentStep < 5 ? (
                  <button
                    type="button"
                    disabled={selectedVideoIds.length === 0 || (currentStep >= 2 && selectedAccountIds.length === 0)}
                    onClick={() => setCurrentStep(currentStep + 1)}
                    className="flex items-center gap-1 rounded-lg bg-primary px-4 py-1.5 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-2xs disabled:opacity-40"
                  >
                    <span>Tiếp tục</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <span />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
