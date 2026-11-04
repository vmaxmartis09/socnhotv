"use client";

import React, { useState } from "react";
import { format, parseISO } from "date-fns";
import { vi } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { Post, PostTarget, socialApi } from "@/lib/api/social";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Film,
  Pencil,
  ShieldCheck,
  X,
} from "@/components/ui/icons";

interface ApprovalsTabProps {
  projectId: string;
}

export function ApprovalsTab({ projectId }: ApprovalsTabProps) {
  const { posts, accounts, loadPosts, openComposer } = useSocialStore();
  const [rejectingPostId, setRejectingPostId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [activeTargetPlatform, setActiveTargetPlatform] = useState<Record<string, string>>({});
  const [bulkApproving, setBulkApproving] = useState(false);

  const pendingPosts = posts.filter(
    (p) =>
      p.status === "pending_approval" ||
      p.targets.some((t) => t.status === "pending_approval")
  );

  const handleApprove = async (postId: string) => {
    try {
      await socialApi.approvePost(projectId, postId, "Duyệt thủ công qua UI Approvals");
      await loadPosts(projectId);
    } catch (err: any) {
      alert(`Lỗi phê duyệt: ${err.message}`);
    }
  };

  const handleBulkApprove = async () => {
    if (!window.confirm(`Bạn có chắc chắn muốn duyệt tất cả ${pendingPosts.length} bài viết đang chờ?`)) {
      return;
    }
    setBulkApproving(true);
    try {
      for (const p of pendingPosts) {
        await socialApi.approvePost(projectId, p.id, "Duyệt hàng loạt");
      }
      await loadPosts(projectId);
    } catch (err: any) {
      alert(`Lỗi: ${err.message}`);
    } finally {
      setBulkApproving(false);
    }
  };

  const handleRejectConfirm = async () => {
    if (!rejectingPostId) return;
    if (!rejectReason.trim()) {
      alert("Vui lòng nhập lý do từ chối");
      return;
    }
    try {
      await socialApi.rejectPost(projectId, rejectingPostId, rejectReason.trim());
      setRejectingPostId(null);
      setRejectReason("");
      await loadPosts(projectId);
    } catch (err: any) {
      alert(`Lỗi từ chối: ${err.message}`);
    }
  };

  if (pendingPosts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-border bg-card">
        <CheckCircle2 className="h-12 w-12 text-emerald-500/80 mb-3" />
        <h3 className="text-base font-semibold text-foreground">Không có bài viết chờ duyệt</h3>
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
          Tất cả các bài viết đã được xem xét hoặc đang ở trạng thái nháp / đã lên lịch.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with bulk action */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Hàng chờ phê duyệt ({pendingPosts.length} bài)
          </h2>
          <p className="text-xs text-muted-foreground">
            Kiểm tra checklist tự động trước khi bấm duyệt để lên lịch xuất bản.
          </p>
        </div>
        <button
          onClick={handleBulkApprove}
          disabled={bulkApproving}
          className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
        >
          <Check className="h-3.5 w-3.5" />
          <span>{bulkApproving ? "Đang duyệt..." : "Duyệt tất cả"}</span>
        </button>
      </div>

      {/* Post cards */}
      <div className="grid gap-6">
        {pendingPosts.map((post) => {
          const media = post.media[0];
          const activePlatform =
            activeTargetPlatform[post.id] || post.targets[0]?.platform || "youtube";
          const currentTarget =
            post.targets.find((t) => t.platform === activePlatform) || post.targets[0];
          const targetAccount = accounts.find((a) => a.id === currentTarget?.account_id);

          // Automated Checklist evaluations
          const hasCaption = Boolean(currentTarget?.caption && currentTarget.caption.trim().length > 0);
          const hasAffiliateDisclosure =
            !currentTarget?.product_link || Boolean(currentTarget?.disclosure_ad);
          const durationOk = !media?.duration_s || media.duration_s <= 300; // Under 5 mins
          const accountConnected = targetAccount ? targetAccount.status === "connected" : true;
          const rightsOk = !post.source_ref || post.source_ref !== "reference_only";

          return (
            <div
              key={post.id}
              className="overflow-hidden rounded-xl border border-border bg-card shadow-sm transition-all hover:border-border/80"
            >
              <div className="grid grid-cols-1 md:grid-cols-[280px_1fr] divide-y md:divide-y-0 md:divide-x divide-border">
                {/* Media Preview Column */}
                <div className="p-4 flex flex-col justify-between bg-muted/20">
                  <div className="space-y-3">
                    <div className="relative aspect-[9/16] w-full max-h-[280px] rounded-lg overflow-hidden border border-border bg-black flex items-center justify-center">
                      {media?.path?.endsWith(".mp4") ? (
                        <video
                          src={media.path}
                          controls
                          className="h-full w-full object-contain"
                          poster={media.thumb}
                        />
                      ) : media?.thumb ? (
                        <img src={media.thumb} alt="" className="h-full w-full object-cover" />
                      ) : (
                        <div className="flex flex-col items-center text-muted-foreground">
                          <Film className="h-8 w-8 mb-1 opacity-50" />
                          <span className="text-[11px]">Xem trước video</span>
                        </div>
                      )}
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm line-clamp-2">{post.title}</h3>
                      <p className="text-[11px] text-muted-foreground font-mono mt-0.5">
                        {post.created_at ? format(parseISO(post.created_at), "dd/MM/yyyy HH:mm") : ""}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Content & Validation Checklist Column */}
                <div className="p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-4">
                    {/* Platform Tabs */}
                    <div className="flex items-center gap-1 border-b border-border pb-2">
                      {post.targets.map((tgt) => (
                        <button
                          key={tgt.id}
                          onClick={() =>
                            setActiveTargetPlatform((prev) => ({
                              ...prev,
                              [post.id]: tgt.platform,
                            }))
                          }
                          className={cn(
                            "rounded-md px-3 py-1 text-xs font-semibold uppercase tracking-wider transition-all",
                            activePlatform === tgt.platform
                              ? "bg-primary text-primary-foreground shadow-2xs"
                              : "text-muted-foreground hover:bg-muted"
                          )}
                        >
                          {tgt.platform}
                        </button>
                      ))}
                    </div>

                    {/* Caption Preview */}
                    <div className="rounded-lg border border-border/80 bg-background/50 p-3 text-xs">
                      <div className="font-medium text-foreground mb-1">
                        {currentTarget?.title && <p className="font-bold mb-1">{currentTarget.title}</p>}
                        <p className="whitespace-pre-wrap text-muted-foreground leading-relaxed">
                          {currentTarget?.caption || "(Chưa có nội dung mô tả)"}
                        </p>
                      </div>
                      {currentTarget?.hashtags && currentTarget.hashtags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {currentTarget.hashtags.map((h, i) => (
                            <span key={i} className="text-primary font-mono text-[10px]">
                              {h.startsWith("#") ? h : `#${h}`}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Automated Validation Checklist */}
                    <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3 text-xs">
                      <div className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                        <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                        Checklist kiểm tra tự động
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                        <div className="flex items-center gap-2">
                          {hasCaption ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <X className="h-3.5 w-3.5 text-rose-500" />
                          )}
                          <span>Đầy đủ Caption & Tiêu đề</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {hasAffiliateDisclosure ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                          )}
                          <span>Có khai báo quảng cáo/affiliate</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {durationOk ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                          )}
                          <span>Độ dài video phù hợp</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {accountConnected ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                          )}
                          <span>Tài khoản sẵn sàng</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {rightsOk ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <X className="h-3.5 w-3.5 text-rose-500" />
                          )}
                          <span>Bản quyền nguồn hợp lệ</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                    <button
                      onClick={() => openComposer(post)}
                      className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted text-foreground"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      <span>Sửa</span>
                    </button>
                    <button
                      onClick={() => setRejectingPostId(post.id)}
                      className="flex items-center gap-1.5 rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-500/20"
                    >
                      <X className="h-3.5 w-3.5" />
                      <span>Từ chối</span>
                    </button>
                    <button
                      onClick={() => handleApprove(post.id)}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>Phê duyệt</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reject Reason Dialog Modal */}
      {rejectingPostId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-xl space-y-4">
            <h3 className="text-base font-semibold text-foreground">Từ chối bài viết</h3>
            <p className="text-xs text-muted-foreground">
              Vui lòng cung cấp lý do để tác giả điều chỉnh lại nội dung:
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Ví dụ: Âm thanh nhỏ, cần bổ sung hashtag #affiliate..."
              className="w-full h-24 rounded-lg border border-border bg-background p-2.5 text-xs focus:ring-1 focus:ring-primary focus:outline-hidden"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setRejectingPostId(null)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                Huỷ
              </button>
              <button
                onClick={handleRejectConfirm}
                className="rounded-lg bg-rose-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-rose-700"
              >
                Xác nhận từ chối
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
