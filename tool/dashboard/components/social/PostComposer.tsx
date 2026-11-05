"use client";

import React, { useState, useEffect } from "react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import { socialApi, type PlatformType } from "@/lib/api/social";
import {
  Calendar,
  Check,
  Film,
  Send,
  Sparkles,
  X,
  Loader2,
  ShieldCheck,
} from "@/components/ui/icons";
import { Clock } from "./icons";

interface PostComposerProps {
  projectId: string;
}

export function PostComposer({ projectId }: PostComposerProps) {
  const {
    isComposerOpen,
    closeComposer,
    editingPost,
    composerInitialDate,
    composerInitialAccount,
    accounts,
    loadAll,
  } = useSocialStore();

  const jobs = useStudioStore((s) => s.jobs);

  const [title, setTitle] = useState("");
  const [mediaPath, setMediaPath] = useState("");
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [scheduledAt, setScheduledAt] = useState("");
  const [requiresApproval, setRequiresApproval] = useState(true);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Available finished render videos
  const completedVideos = jobs
    .filter((j) => (j.status === "completed" || (j as any).status === "done") && j.outputUrl)
    .map((j) => ({
      id: j.id,
      name: `Job #${j.id.slice(0, 10)} (${j.model || "Video"})`,
      url: j.outputUrl!,
    }));

  useEffect(() => {
    if (!isComposerOpen) return;

    if (editingPost) {
      setTitle(editingPost.title || "");
      setMediaPath(editingPost.media?.[0]?.path || "");
      const accIds = editingPost.targets.map((t) => t.account_id);
      setSelectedAccountIds(accIds);
      const firstTarget = editingPost.targets[0];
      setCaption(firstTarget?.caption || "");
      setHashtags(firstTarget?.hashtags || []);
      setScheduledAt(firstTarget?.scheduled_at ? firstTarget.scheduled_at.slice(0, 16) : "");
      setRequiresApproval(editingPost.status === "draft");
    } else {
      setTitle("");
      // If we have completed videos, default to the latest one
      if (completedVideos.length > 0) {
        setMediaPath(completedVideos[0].url);
        setTitle(completedVideos[0].name);
      } else {
        setMediaPath("");
      }

      const initAcc = composerInitialAccount || accounts[0]?.id;
      setSelectedAccountIds(initAcc ? [initAcc] : accounts.map((a) => a.id));
      setCaption("");
      setHashtags(accounts[0]?.default_hashtags || ["#socnhotv"]);

      const defaultDate = composerInitialDate || format(new Date(), "yyyy-MM-dd");
      setScheduledAt(`${defaultDate}T19:00`);
      setRequiresApproval(true);
    }
    setErrorMessage(null);
  }, [isComposerOpen, editingPost, composerInitialDate, composerInitialAccount, accounts]);

  if (!isComposerOpen) return null;

  const handleToggleAccount = (id: string) => {
    setSelectedAccountIds((prev) =>
      prev.includes(id) ? (prev.length > 1 ? prev.filter((x) => x !== id) : prev) : [...prev, id]
    );
  };

  const handleSuggestTime = async () => {
    if (selectedAccountIds.length === 0) return;
    setIsSuggesting(true);
    try {
      const res = await socialApi.suggestTime(projectId, selectedAccountIds[0]);
      if (res.suggested_time) {
        setScheduledAt(res.suggested_time.slice(0, 16));
      }
    } catch {
      // Fallback: 19:30 tonight
      const today = format(new Date(), "yyyy-MM-dd");
      setScheduledAt(`${today}T19:30`);
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleGenerateCaption = async () => {
    if (!title.trim()) {
      setErrorMessage("Vui lòng nhập tiêu đề hoặc chủ đề video trước.");
      return;
    }
    setIsGenerating(true);
    setErrorMessage(null);
    try {
      const selectedPlatforms = selectedAccountIds
        .map((id) => accounts.find((a) => a.id === id)?.platform)
        .filter(Boolean) as string[];

      const res = await socialApi.generateCaptionVariants(projectId, {
        title,
        caption,
        hashtags,
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms : ["tiktok", "youtube"],
      });

      const firstVariant = Object.values(res.variants || {})[0] as any;
      if (firstVariant) {
        setCaption(firstVariant.caption || caption);
        setHashtags(firstVariant.hashtags || hashtags);
      }
    } catch (err: any) {
      setErrorMessage(`Lỗi sinh caption: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = async (action: "schedule" | "publish_now") => {
    if (!title.trim()) {
      setErrorMessage("Vui lòng nhập tiêu đề bài viết.");
      return;
    }
    if (selectedAccountIds.length === 0) {
      setErrorMessage("Vui lòng chọn ít nhất 1 tài khoản mạng xã hội.");
      return;
    }

    if (action === "publish_now") {
      if (!window.confirm("Bạn có chắc chắn muốn ĐĂNG NGAY lên các tài khoản đã chọn?")) {
        return;
      }
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const targetsPayload = selectedAccountIds.map((accId) => {
        const acc = accounts.find((a) => a.id === accId);
        return {
          account_id: accId,
          platform: (acc?.platform || "tiktok") as PlatformType,
          caption,
          hashtags,
          title,
          scheduled_at: scheduledAt ? `${scheduledAt}:00+07:00` : new Date().toISOString(),
          status: requiresApproval ? "draft" : "scheduled",
        };
      });

      let savedPost;
      if (editingPost) {
        savedPost = await socialApi.updatePost(projectId, editingPost.id, {
          title,
          targets: targetsPayload as any,
          status: requiresApproval ? "draft" : "scheduled",
        });
      } else {
        savedPost = await socialApi.createPost(projectId, {
          title,
          media: mediaPath ? [{ kind: "video", path: mediaPath, duration_s: 60 }] : [],
          targets: targetsPayload as any,
          status: requiresApproval ? "draft" : "scheduled",
        });
      }

      if (action === "publish_now" && savedPost?.id) {
        await socialApi.publishNow(projectId, savedPost.id);
      }

      await loadAll(projectId);
      closeComposer();
    } catch (err: any) {
      setErrorMessage(`Lỗi lưu bài: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-background/80 backdrop-blur-sm">
      <div className="relative flex flex-col w-full max-w-xl max-h-[92vh] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden select-none">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-accent/30 shrink-0">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">
              {editingPost ? "Sửa lịch đăng" : "Lên lịch đăng video"}
            </h3>
          </div>
          <button
            onClick={closeComposer}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 scroll-quiet text-xs">
          {errorMessage && (
            <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 p-2.5 text-rose-500 text-xs">
              {errorMessage}
            </div>
          )}

          {/* Video Media Source */}
          <div className="space-y-1">
            <label className="font-semibold text-foreground flex items-center gap-1.5">
              <Film className="h-3.5 w-3.5 text-primary" />
              Video xuất bản:
            </label>
            {completedVideos.length > 0 ? (
              <select
                value={mediaPath}
                onChange={(e) => setMediaPath(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
              >
                <option value="">-- Chọn video từ danh sách Jobs hoàn tất --</option>
                {completedVideos.map((v) => (
                  <option key={v.id} value={v.url}>
                    {v.name}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="Đường dẫn file video (vd: output/final_render.mp4)..."
                value={mediaPath}
                onChange={(e) => setMediaPath(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
              />
            )}
          </div>

          {/* Post Title */}
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Tiêu đề bài viết / Video:</label>
            <input
              type="text"
              placeholder="Nhập tiêu đề xuất bản..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
            />
          </div>

          {/* Social Accounts */}
          <div className="space-y-1.5">
            <label className="font-semibold text-foreground">Chọn kênh đăng ({accounts.length} kênh):</label>
            <div className="flex flex-wrap gap-2">
              {accounts.map((acc) => {
                const isSelected = selectedAccountIds.includes(acc.id);
                return (
                  <button
                    key={acc.id}
                    type="button"
                    onClick={() => handleToggleAccount(acc.id)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-3.5 w-3.5 items-center justify-center rounded border",
                        isSelected ? "border-primary bg-primary text-white" : "border-border"
                      )}
                    >
                      {isSelected && <Check className="h-2.5 w-2.5" />}
                    </div>
                    <span>{acc.display_name || acc.handle}</span>
                    <span className="text-[10px] uppercase text-muted-foreground font-mono">
                      ({acc.platform})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Caption & Hashtags */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-foreground">Caption & Nội dung bài viết:</label>
              <button
                type="button"
                onClick={handleGenerateCaption}
                disabled={isGenerating || !title.trim()}
                className="flex items-center gap-1 rounded bg-primary/10 text-primary px-2 py-0.5 text-[11px] font-medium hover:bg-primary/20 disabled:opacity-40 transition-colors"
              >
                {isGenerating ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Sparkles className="h-3 w-3" />
                )}
                <span>Tự sinh Caption & Hashtag</span>
              </button>
            </div>
            <textarea
              rows={3}
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Nhập nội dung caption..."
              className="w-full rounded-lg border border-border bg-background p-2.5 text-xs text-foreground outline-none focus:border-primary font-sans leading-relaxed"
            />
            <input
              type="text"
              value={hashtags.join(" ")}
              onChange={(e) =>
                setHashtags(
                  e.target.value
                    .split(/\s+/)
                    .filter(Boolean)
                    .map((h) => (h.startsWith("#") ? h : `#${h}`))
                )
              }
              placeholder="Hashtags (vd: #socnhotv #hoathinh3d)..."
              className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono"
            />
          </div>

          {/* Schedule Time & Golden Hour */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-foreground flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-primary" />
                Thời gian đăng bài:
              </label>
              <button
                type="button"
                onClick={handleSuggestTime}
                disabled={isSuggesting}
                className="text-[11px] text-primary hover:underline"
              >
                {isSuggesting ? "Đang tính..." : "⚡ Gợi ý giờ vàng của kênh"}
              </button>
            </div>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
            />
          </div>

          {/* Approval switch */}
          <div className="flex items-center justify-between rounded-lg border border-border bg-accent/20 p-2.5">
            <div className="space-y-0.5">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                Duyệt trước khi đăng
              </span>
              <p className="text-[11px] text-muted-foreground">
                Lưu ở trạng thái Nháp (cần bấm duyệt 1 lần trước khi đẩy lên kênh)
              </p>
            </div>
            <input
              type="checkbox"
              checked={requiresApproval}
              onChange={(e) => setRequiresApproval(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary cursor-pointer"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-accent/20 shrink-0">
          <button
            type="button"
            onClick={closeComposer}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-accent"
          >
            Hủy
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSubmit("schedule")}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors shadow-2xs"
            >
              <Calendar className="h-3.5 w-3.5" />
              <span>Hẹn giờ</span>
            </button>

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSubmit("publish_now")}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors shadow-2xs"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Đăng ngay</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
