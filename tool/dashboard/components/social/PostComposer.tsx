"use client";

import React, { useState, useEffect } from "react";
import { format, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import {
  PlatformType,
  Post,
  PostTarget,
  SocialAccount,
  socialApi,
} from "@/lib/api/social";
import {
  Calendar,
  Check,
  Film,
  Link2,
  Send,
  Sparkles,
  Upload,
  X,
  PanelRightClose,
} from "@/components/ui/icons";
import { Clock } from "./icons";

interface PostComposerProps {
  projectId: string;
}

const CHAR_LIMITS: Record<PlatformType, number> = {
  tiktok: 2200,
  youtube: 5000,
  instagram: 2200,
  facebook: 5000,
  douyin: 1000,
  threads: 500,
  x: 280,
};

export function PostComposer({ projectId }: PostComposerProps) {
  const {
    isComposerOpen,
    closeComposer,
    editingPost,
    composerInitialDate,
    composerInitialAccount,
    accounts,
    loadPosts,
    loadCalendar,
  } = useSocialStore();

  const [title, setTitle] = useState("");
  const [mediaPath, setMediaPath] = useState("");
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [activeTabAccount, setActiveTabAccount] = useState<string>("");

  // Targets state per account_id
  const [targetsData, setTargetsData] = useState<
    Record<
      string,
      {
        caption: string;
        hashtags: string[];
        scheduled_at: string;
        title: string;
        description: string;
        tags: string[];
        privacy: "public" | "unlisted" | "private";
        made_for_kids: boolean;
        cover_time_s: number;
        first_comment: string;
        product_link: string;
        disclosure_ad: boolean;
      }
    >
  >({});

  const [generatingVariants, setGeneratingVariants] = useState(false);
  const [suggestingTime, setSuggestingTime] = useState(false);
  const [saving, setSaving] = useState(false);

  // Initialize or reset form when composer opens
  useEffect(() => {
    if (!isComposerOpen) return;

    if (editingPost) {
      setTitle(editingPost.title);
      setMediaPath(editingPost.media[0]?.path || "");
      const accIds = editingPost.targets.map((t) => t.account_id);
      setSelectedAccountIds(accIds);
      setActiveTabAccount(accIds[0] || "");

      const tMap: Record<string, any> = {};
      for (const t of editingPost.targets) {
        tMap[t.account_id] = {
          caption: t.caption || "",
          hashtags: t.hashtags || [],
          scheduled_at: t.scheduled_at || "",
          title: t.title || editingPost.title,
          description: t.description || "",
          tags: t.tags || [],
          privacy: t.privacy || "public",
          made_for_kids: Boolean(t.made_for_kids),
          cover_time_s: t.cover_time_s || 0,
          first_comment: t.first_comment || "",
          product_link: t.product_link || "",
          disclosure_ad: Boolean(t.disclosure_ad),
        };
      }
      setTargetsData(tMap);
    } else {
      // New post defaults
      setTitle("Video mới");
      setMediaPath("");
      const initialAcc = composerInitialAccount || accounts[0]?.id || "";
      const accList = initialAcc ? [initialAcc] : [];
      setSelectedAccountIds(accList);
      setActiveTabAccount(initialAcc);

      const defaultTime = composerInitialDate
        ? `${composerInitialDate}T19:00:00+07:00`
        : `${format(new Date(), "yyyy-MM-dd")}T19:00:00+07:00`;

      const tMap: Record<string, any> = {};
      for (const a of accounts) {
        tMap[a.id] = {
          caption: "",
          hashtags: [...a.default_hashtags],
          scheduled_at: defaultTime,
          title: "Video mới",
          description: "",
          tags: [...a.default_hashtags],
          privacy: "public",
          made_for_kids: false,
          cover_time_s: 0,
          first_comment: "",
          product_link: "",
          disclosure_ad: false,
        };
      }
      setTargetsData(tMap);
    }
  }, [isComposerOpen, editingPost, composerInitialDate, composerInitialAccount, accounts]);

  if (!isComposerOpen) return null;

  const toggleAccountSelection = (accId: string) => {
    let next: string[];
    if (selectedAccountIds.includes(accId)) {
      next = selectedAccountIds.filter((id) => id !== accId);
    } else {
      next = [...selectedAccountIds, accId];
    }
    setSelectedAccountIds(next);
    if (!next.includes(activeTabAccount)) {
      setActiveTabAccount(next[0] || "");
    }
  };

  const currentAccount = accounts.find((a) => a.id === activeTabAccount);
  const currentTarget = activeTabAccount ? targetsData[activeTabAccount] : null;

  const updateCurrentTarget = (field: string, value: any) => {
    if (!activeTabAccount) return;
    setTargetsData((prev) => ({
      ...prev,
      [activeTabAccount]: {
        ...(prev[activeTabAccount] || {}),
        [field]: value,
      },
    }));
  };

  // AI / Rule-based caption generator
  const handleGenerateVariants = async () => {
    if (!title) return;
    setGeneratingVariants(true);
    try {
      const activePlatforms = selectedAccountIds
        .map((id) => accounts.find((a) => a.id === id)?.platform)
        .filter(Boolean) as string[];

      const cur = currentTarget;
      const res = await socialApi.generateCaptionVariants(projectId, {
        title,
        caption: cur?.caption || "",
        hashtags: cur?.hashtags || [],
        platforms: activePlatforms.length > 0 ? activePlatforms : ["tiktok", "youtube"],
        product_link: cur?.product_link || "",
        footer: currentAccount?.default_caption_footer || "",
      });

      // Apply variants to each selected account
      setTargetsData((prev) => {
        const next = { ...prev };
        for (const accId of selectedAccountIds) {
          const acc = accounts.find((a) => a.id === accId);
          if (acc && res.variants[acc.platform]) {
            const v = res.variants[acc.platform];
            next[accId] = {
              ...(next[accId] || {}),
              caption: v.caption || next[accId]?.caption,
              hashtags: v.hashtags || next[accId]?.hashtags,
              title: v.title || next[accId]?.title,
              description: v.description || next[accId]?.description,
              disclosure_ad: v.disclosure_ad ?? next[accId]?.disclosure_ad,
            };
          }
        }
        return next;
      });
    } catch (err: any) {
      alert(`Lỗi sinh caption: ${err.message}`);
    } finally {
      setGeneratingVariants(false);
    }
  };

  // Suggest optimal time
  const handleSuggestTime = async () => {
    if (!activeTabAccount) return;
    setSuggestingTime(true);
    try {
      const res = await socialApi.suggestTime(
        projectId,
        activeTabAccount,
        currentTarget?.scheduled_at
      );
      if (res.suggested_time) {
        updateCurrentTarget("scheduled_at", res.suggested_time);
      }
    } catch (err: any) {
      alert(`Lỗi gợi ý giờ: ${err.message}`);
    } finally {
      setSuggestingTime(false);
    }
  };

  const handleSave = async (targetStatus: "draft" | "pending_approval" | "scheduled") => {
    if (!title.trim()) {
      alert("Vui lòng nhập tiêu đề bài viết");
      return;
    }
    if (selectedAccountIds.length === 0) {
      alert("Vui lòng chọn ít nhất 1 tài khoản đăng bài");
      return;
    }

    setSaving(true);
    try {
      const targetsPayload: PostTarget[] = selectedAccountIds.map((accId) => {
        const acc = accounts.find((a) => a.id === accId);
        const t = targetsData[accId];
        return {
          id: `tgt_${accId}_${Date.now().toString(36)}`,
          account_id: accId,
          platform: acc?.platform || "youtube",
          scheduled_at: t?.scheduled_at || null,
          caption: t?.caption || "",
          hashtags: t?.hashtags || [],
          title: t?.title || title,
          description: t?.description || "",
          tags: t?.tags || [],
          privacy: t?.privacy || "public",
          made_for_kids: Boolean(t?.made_for_kids),
          cover_time_s: t?.cover_time_s || 0,
          first_comment: t?.first_comment || "",
          product_link: t?.product_link || "",
          disclosure_ad: Boolean(t?.disclosure_ad),
          status: targetStatus,
        };
      });

      const postPayload: Partial<Post> = {
        title: title.trim(),
        media: mediaPath ? [{ path: mediaPath, duration_s: 60, kind: "video" }] : [],
        targets: targetsPayload,
        status: targetStatus,
      };

      if (editingPost) {
        await socialApi.updatePost(projectId, editingPost.id, postPayload);
        if (targetStatus === "pending_approval") {
          await socialApi.submitPost(projectId, editingPost.id);
        } else if (targetStatus === "scheduled") {
          const tTimes: Record<string, string> = {};
          targetsPayload.forEach((t) => {
            if (t.scheduled_at) tTimes[t.id] = t.scheduled_at;
          });
          await socialApi.schedulePost(projectId, editingPost.id, tTimes);
        }
      } else {
        const created = await socialApi.createPost(projectId, postPayload);
        if (targetStatus === "pending_approval") {
          await socialApi.submitPost(projectId, created.id);
        }
      }

      await loadPosts(projectId);
      await loadCalendar(projectId);
      closeComposer();
    } catch (err: any) {
      alert(`Lỗi lưu bài: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const limit = currentAccount ? CHAR_LIMITS[currentAccount.platform] || 2200 : 2200;
  const currentLength = currentTarget?.caption.length || 0;

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-2xl flex-col border-l border-border bg-card shadow-2xl backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border p-4 bg-muted/20">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            {editingPost ? "Chỉnh sửa bài viết" : "Soạn bài viết đa nền tảng"}
          </h2>
          <p className="text-xs text-muted-foreground">
            Một lần soạn nội dung, tự động tối ưu caption và kích thước cho từng kênh.
          </p>
        </div>
        <button
          onClick={closeComposer}
          className="rounded-lg p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground"
        >
          <PanelRightClose className="h-5 w-5" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs">
        {/* Title & Media Input */}
        <div className="space-y-3">
          <div>
            <label className="font-semibold text-foreground block mb-1">Tiêu đề bài viết</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ví dụ: Tập 2: Sóc Nhỏ Khám Phá Rừng Xanh"
              className="w-full rounded-lg border border-border bg-background p-2.5 text-sm font-medium focus:ring-1 focus:ring-primary focus:outline-hidden"
            />
          </div>

          <div>
            <label className="font-semibold text-foreground block mb-1">
              Video / Tệp Media (từ Renders hoặc Library)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={mediaPath}
                onChange={(e) => setMediaPath(e.target.value)}
                placeholder="content/episodes/soc-nho/video.mp4"
                className="flex-1 rounded-lg border border-border bg-background p-2 font-mono text-xs focus:ring-1 focus:ring-primary focus:outline-hidden"
              />
              <button
                type="button"
                onClick={() => setMediaPath("content/episodes/soc-nho-sau-rang/video.mp4")}
                className="rounded-lg border border-border bg-muted/40 px-3 py-1.5 font-medium hover:bg-muted"
              >
                Chọn mẫu
              </button>
            </div>
          </div>
        </div>

        {/* Account Selector Chips */}
        <div>
          <label className="font-semibold text-foreground block mb-1.5">
            Đăng lên các tài khoản:
          </label>
          <div className="flex flex-wrap gap-2">
            {accounts.map((acc) => {
              const isSelected = selectedAccountIds.includes(acc.id);
              return (
                <button
                  key={acc.id}
                  type="button"
                  onClick={() => toggleAccountSelection(acc.id)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold transition-all",
                    isSelected
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-background text-muted-foreground hover:bg-muted"
                  )}
                >
                  <span className="uppercase text-[9px] px-1 py-0.2 rounded bg-background/60">
                    {acc.platform}
                  </span>
                  <span>{acc.display_name}</span>
                  {isSelected && <Check className="h-3 w-3" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Multi-Platform Target Editor */}
        {selectedAccountIds.length > 0 && (
          <div className="rounded-xl border border-border bg-background p-4 space-y-4">
            {/* Account Tabs */}
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div className="flex items-center gap-1">
                {selectedAccountIds.map((accId) => {
                  const acc = accounts.find((a) => a.id === accId);
                  return (
                    <button
                      key={accId}
                      type="button"
                      onClick={() => setActiveTabAccount(accId)}
                      className={cn(
                        "rounded-md px-3 py-1 text-xs font-semibold uppercase tracking-wider transition-all",
                        activeTabAccount === accId
                          ? "bg-primary text-primary-foreground shadow-2xs"
                          : "text-muted-foreground hover:bg-muted"
                      )}
                    >
                      {acc?.display_name || accId}
                    </button>
                  );
                })}
              </div>

              {/* Generate AI caption variants button */}
              <button
                type="button"
                onClick={handleGenerateVariants}
                disabled={generatingVariants}
                className="flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline disabled:opacity-50"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{generatingVariants ? "Đang sinh..." : "Sinh caption cho tất cả"}</span>
              </button>
            </div>

            {/* Target Fields */}
            {currentTarget && currentAccount && (
              <div className="space-y-3">
                {/* Scheduled Time + Suggest button */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="font-medium text-muted-foreground block mb-1">
                      Giờ đăng dự kiến
                    </label>
                    <div className="flex gap-1.5">
                      <input
                        type="datetime-local"
                        value={currentTarget.scheduled_at ? currentTarget.scheduled_at.slice(0, 16) : ""}
                        onChange={(e) =>
                          updateCurrentTarget(
                            "scheduled_at",
                            e.target.value ? `${e.target.value}:00+07:00` : ""
                          )
                        }
                        className="flex-1 rounded-lg border border-border bg-background p-1.5 text-xs font-mono"
                      />
                      <button
                        type="button"
                        onClick={handleSuggestTime}
                        disabled={suggestingTime}
                        className="rounded-lg border border-border bg-muted/40 px-2 py-1 font-semibold hover:bg-muted text-primary"
                        title="Tự động tìm khung giờ vàng trống"
                      >
                        <Clock className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="font-medium text-muted-foreground block mb-1">
                      Chế độ hiển thị
                    </label>
                    <select
                      value={currentTarget.privacy}
                      onChange={(e) => updateCurrentTarget("privacy", e.target.value)}
                      className="w-full rounded-lg border border-border bg-background p-1.5 text-xs"
                    >
                      <option value="public">Công khai (Public)</option>
                      <option value="unlisted">Không công khai (Unlisted)</option>
                      <option value="private">Riêng tư (Private)</option>
                    </select>
                  </div>
                </div>

                {/* YouTube Specific Fields */}
                {currentAccount.platform === "youtube" && (
                  <div className="space-y-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                    <div className="flex justify-between items-center text-[11px] font-semibold text-red-600 dark:text-red-400">
                      <span>Tiêu đề YouTube (Tối đa 100 ký tự)</span>
                      <span>{(currentTarget.title || "").length} / 100</span>
                    </div>
                    <input
                      type="text"
                      maxLength={100}
                      value={currentTarget.title || ""}
                      onChange={(e) => updateCurrentTarget("title", e.target.value)}
                      className="w-full rounded-md border border-border bg-background p-1.5 text-xs"
                    />
                    <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground mt-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={currentTarget.made_for_kids}
                        onChange={(e) => updateCurrentTarget("made_for_kids", e.target.checked)}
                      />
                      <span>Nội dung dành cho trẻ em (Made for Kids)</span>
                    </label>
                  </div>
                )}

                {/* Caption / Description Field */}
                <div>
                  <div className="flex justify-between items-center text-muted-foreground mb-1">
                    <span className="font-medium">Nội dung Caption</span>
                    <span
                      className={cn(
                        "font-mono text-[11px]",
                        currentLength > limit ? "text-rose-500 font-bold" : "text-muted-foreground"
                      )}
                    >
                      {currentLength} / {limit} ký tự
                    </span>
                  </div>
                  <textarea
                    rows={4}
                    value={currentTarget.caption}
                    onChange={(e) => updateCurrentTarget("caption", e.target.value)}
                    placeholder="Viết caption cuốn hút, hook trong 3 dòng đầu..."
                    className="w-full rounded-lg border border-border bg-background p-2.5 text-xs leading-relaxed focus:ring-1 focus:ring-primary focus:outline-hidden"
                  />
                </div>

                {/* Hashtags Input */}
                <div>
                  <label className="font-medium text-muted-foreground block mb-1">Hashtags</label>
                  <input
                    type="text"
                    value={currentTarget.hashtags.join(" ")}
                    onChange={(e) =>
                      updateCurrentTarget(
                        "hashtags",
                        e.target.value
                          .split(/[\s,]+/)
                          .filter(Boolean)
                          .map((h) => (h.startsWith("#") ? h : `#${h}`))
                      )
                    }
                    placeholder="#socnhotv #cartoon #trending"
                    className="w-full rounded-lg border border-border bg-background p-2 text-xs font-mono focus:ring-1 focus:ring-primary focus:outline-hidden"
                  />
                </div>

                {/* Affiliate / Product Link */}
                <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-2">
                  <label className="font-medium text-foreground block">
                    Liên kết sản phẩm / Affiliate (TikTok Shop, Shopee...)
                  </label>
                  <input
                    type="url"
                    value={currentTarget.product_link}
                    onChange={(e) => updateCurrentTarget("product_link", e.target.value)}
                    placeholder="https://shop.tiktok.com/view/product/..."
                    className="w-full rounded-md border border-border bg-background p-1.5 text-xs font-mono"
                  />
                  <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground cursor-pointer">
                    <input
                      type="checkbox"
                      checked={currentTarget.disclosure_ad}
                      onChange={(e) => updateCurrentTarget("disclosure_ad", e.target.checked)}
                    />
                    <span>Khai báo nhãn nội dung quảng cáo / tài trợ (#ad)</span>
                  </label>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Mobile Phone Simulation Preview */}
        {currentTarget && currentAccount && (
          <div className="rounded-xl border border-border bg-muted/10 p-4 space-y-2">
            <h4 className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
              Mô phỏng hiển thị trên {currentAccount.platform}
            </h4>
            <div className="mx-auto max-w-[280px] rounded-2xl border-4 border-zinc-800 bg-black text-white p-3 shadow-lg space-y-2">
              <div className="aspect-[9/16] rounded-xl bg-zinc-900 flex items-center justify-center text-zinc-500 overflow-hidden relative">
                {mediaPath ? (
                  <video src={mediaPath} className="h-full w-full object-cover" />
                ) : (
                  <Film className="h-10 w-10 opacity-40" />
                )}
                {/* Floating caption overlay */}
                <div className="absolute inset-x-2 bottom-2 bg-black/60 backdrop-blur-xs p-2 rounded-lg text-[10px] leading-snug">
                  <p className="font-bold">{currentAccount.handle}</p>
                  <p className="line-clamp-2 text-zinc-300 mt-0.5">
                    {currentTarget.caption || title}
                  </p>
                  <span className="text-zinc-400 font-semibold cursor-pointer">...xem thêm</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Drawer Footer Actions */}
      <div className="flex items-center justify-between border-t border-border p-4 bg-muted/20">
        <button
          type="button"
          onClick={() => handleSave("draft")}
          disabled={saving}
          className="rounded-lg border border-border bg-background px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-50"
        >
          Lưu bản nháp
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleSave("pending_approval")}
            disabled={saving}
            className="rounded-lg bg-amber-600 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-amber-700 disabled:opacity-50"
          >
            Gửi phê duyệt
          </button>
          <button
            type="button"
            onClick={() => handleSave("scheduled")}
            disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Lên lịch ngay</span>
          </button>
        </div>
      </div>
    </div>
  );
}
