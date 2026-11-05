"use client";
import { confirm } from "@/lib/confirm";

import React from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import { X, Calendar, Clock, Film, ExternalLink, Trash2, CheckCircle, RefreshCw, AlertCircle } from "@/components/ui/icons";
import { VideoThumb } from "./VideoThumb";
import { StatusBadge } from "./StatusBadge";
import { AccountChip } from "./AccountChip";
import { LibraryVideo, VideoPostTarget, SocialAccount } from "@/lib/api/social";

interface DetailDrawerProps {
  onPlanVideo?: (videoId: string) => void;
  onEditPost?: (target: VideoPostTarget) => void;
  onRefresh?: () => void;
}

export function DetailDrawer({ onPlanVideo, onEditPost, onRefresh }: DetailDrawerProps) {
  const { hubSelectedEntity, setHubSelectedEntity, accounts, bulkAction } = useSocialStore();
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const [actionLoading, setActionLoading] = React.useState(false);

  if (!hubSelectedEntity) return null;

  const { type, data } = hubSelectedEntity;

  const handleClose = () => {
    setHubSelectedEntity(null);
  };

  const handleReschedule = async (targetId: string, hours: number) => {
    if (!activeProjectId) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, [targetId], "reschedule", { shift_hours: hours });
      onRefresh?.();
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async (targetId: string) => {
    if (!activeProjectId) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, [targetId], "approve");
      onRefresh?.();
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelPost = async (targetId: string) => {
    if (!activeProjectId) return;
    if (!(await confirm({ tone: "danger", title: "Hủy bài đăng", message: "Bạn có chắc chắn muốn hủy bài đăng này?" }))) return;
    setActionLoading(true);
    try {
      await bulkAction(activeProjectId, [targetId], "cancel");
      onRefresh?.();
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <aside
      aria-label="Ngăn chi tiết thực thể"
      className={cn(
        "flex flex-col border-l border-border bg-card/95 backdrop-blur-md z-20 shrink-0",
        "w-full lg:w-96 max-w-full overflow-y-auto transition-all"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-semibold tracking-wider text-muted-foreground">
            {type === "video" ? "Chi tiết Video" : type === "post" ? "Chi tiết Bài đăng" : "Chi tiết Tài khoản"}
          </span>
        </div>
        <button
          type="button"
          onClick={handleClose}
          aria-label="Đóng ngăn chi tiết"
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content Body */}
      <div className="p-4 space-y-5 text-sm">
        {type === "video" && (
          <VideoDetailView
            video={data as LibraryVideo}
            accounts={accounts}
            onPlanVideo={onPlanVideo}
          />
        )}

        {type === "post" && (
          <PostDetailView
            post={data as VideoPostTarget}
            accounts={accounts}
            actionLoading={actionLoading}
            onApprove={handleApprove}
            onReschedule={handleReschedule}
            onCancel={handleCancelPost}
          />
        )}

        {type === "account" && (
          <AccountDetailView account={data as SocialAccount} />
        )}
      </div>
    </aside>
  );
}

function VideoDetailView({
  video,
  accounts,
  onPlanVideo,
}: {
  video: LibraryVideo;
  accounts: SocialAccount[];
  onPlanVideo?: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      {/* Thumbnail preview */}
      <div className="rounded-lg overflow-clip border border-border bg-black/40">
        <VideoThumb
          thumb={video.thumb}
          title={video.title}
          durationSec={video.duration_s || video.duration_sec}
          aspectRatio={video.aspect_ratio}
          className="w-full h-44"
        />
      </div>

      <div>
        <h3 className="font-semibold text-base text-foreground leading-snug">{video.title}</h3>
        <p className="text-xs text-muted-foreground mt-0.5">{video.id}</p>
      </div>

      {/* Metadata pills */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-muted/40 p-2.5 rounded-md border border-border/50">
          <span className="text-muted-foreground block mb-0.5">Thời lượng</span>
          <span className="font-medium">{(video.duration_s || video.duration_sec) ? `${Math.round(video.duration_s || video.duration_sec!)} giây` : "Chưa rõ"}</span>
        </div>
        <div className="bg-muted/40 p-2.5 rounded-md border border-border/50">
          <span className="text-muted-foreground block mb-0.5">Tỉ lệ khung hình</span>
          <span className="font-medium">{video.aspect_ratio || "9:16"}</span>
        </div>
      </div>

      {/* Per-account publishing status */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Trạng thái theo Tài khoản
        </h4>
        <div className="space-y-2">
          {accounts.map((acc) => {
            const postInfo = video.posts_by_account?.find((p) => p.account_id === acc.id);
            const status = postInfo?.status || "unposted";

            return (
              <div
                key={acc.id}
                className="flex items-center justify-between p-2 rounded-md bg-muted/30 border border-border/40 text-xs"
              >
                <div className="flex items-center gap-2">
                  <AccountChip account={acc} size="sm" />
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={status} size="sm" />
                  {postInfo?.published_url && (
                    <a
                      href={postInfo.published_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center gap-0.5"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => onPlanVideo?.(video.id)}
          className="w-full py-2.5 px-3 rounded-lg bg-primary text-primary-foreground font-medium text-xs flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors shadow-sm"
        >
          <Calendar className="w-4 h-4" />
          Lên kế hoạch đăng video này
        </button>
      </div>
    </div>
  );
}

function PostDetailView({
  post,
  accounts,
  actionLoading,
  onApprove,
  onReschedule,
  onCancel,
}: {
  post: VideoPostTarget;
  accounts: SocialAccount[];
  actionLoading: boolean;
  onApprove: (id: string) => void;
  onReschedule: (id: string, h: number) => void;
  onCancel: (id: string) => void;
}) {
  const account = accounts.find((a) => a.id === post.account_id);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <StatusBadge status={post.status} size="md" />
        <span className="text-xs text-muted-foreground font-mono">{post.target_id.slice(0, 10)}</span>
      </div>

      {/* Target Account */}
      {account && (
        <div className="p-2.5 rounded-lg bg-muted/40 border border-border/50">
          <span className="text-xs text-muted-foreground block mb-1">Tài khoản đích</span>
          <AccountChip account={account} size="md" />
        </div>
      )}

      {/* Schedule Time */}
      <div className="p-2.5 rounded-lg bg-muted/40 border border-border/50">
        <span className="text-xs text-muted-foreground block mb-1">Thời gian hẹn</span>
        <div className="flex items-center gap-1.5 text-xs font-medium">
          <Clock className="w-3.5 h-3.5 text-muted-foreground" />
          {post.scheduled_at ? new Date(post.scheduled_at).toLocaleString("vi-VN") : "Chưa hẹn giờ (Bản nháp)"}
        </div>
      </div>

      {/* Caption Content */}
      <div className="p-2.5 rounded-lg bg-muted/40 border border-border/50 space-y-1.5">
        <span className="text-xs text-muted-foreground block">Nội dung / Caption</span>
        <p className="text-xs text-foreground whitespace-pre-wrap line-clamp-6 leading-relaxed">
          {post.caption || "Không có caption"}
        </p>
        {post.hashtags && post.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {post.hashtags.map((h, i) => (
              <span key={`${h}-${i}`} className="text-[11px] text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                #{h.replace(/^#/, "")}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Quick Action buttons */}
      <div className="pt-2 space-y-2">
        {post.status === "pending_approval" && (
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onApprove(post.target_id)}
            className="w-full py-2 px-3 rounded-md bg-emerald-600 text-white font-medium text-xs flex items-center justify-center gap-1.5 hover:bg-emerald-500 transition-colors"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            Duyệt bài đăng này
          </button>
        )}

        {post.scheduled_at && post.status !== "published" && (
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => onReschedule(post.target_id, 2)}
              className="py-1.5 px-2 rounded-md bg-muted hover:bg-muted/80 text-foreground text-xs flex items-center justify-center gap-1 transition-colors border border-border"
            >
              <Clock className="w-3 h-3 text-muted-foreground" />
              Lùi +2 giờ
            </button>
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => onReschedule(post.target_id, 24)}
              className="py-1.5 px-2 rounded-md bg-muted hover:bg-muted/80 text-foreground text-xs flex items-center justify-center gap-1 transition-colors border border-border"
            >
              <Calendar className="w-3 h-3 text-muted-foreground" />
              Lùi +1 ngày
            </button>
          </div>
        )}

        {post.status !== "published" && (
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onCancel(post.target_id)}
            className="w-full py-2 px-3 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 font-medium text-xs flex items-center justify-center gap-1.5 transition-colors border border-destructive/20"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Hủy bài đăng
          </button>
        )}
      </div>
    </div>
  );
}

function AccountDetailView({ account }: { account: SocialAccount }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {account.avatar ? (
          <img decoding="async" loading="lazy" src={account.avatar} alt={account.display_name} className="w-12 h-12 rounded-full border border-border" />
        ) : (
          <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-lg">
            {account.display_name?.slice(0, 2).toUpperCase() || "AC"}
          </div>
        )}
        <div>
          <h3 className="font-semibold text-foreground">{account.display_name}</h3>
          <p className="text-xs text-muted-foreground font-mono">{account.handle}</p>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-muted/40 border border-border/50 space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Nền tảng</span>
          <span className="font-medium uppercase">{account.platform}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Chế độ kết nối</span>
          <span className="font-medium">{account.auth_mode === "oauth" ? "OAuth chính thức" : "Gói đăng tay"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Nhóm tài khoản</span>
          <span className="font-medium">{account.group || "Chưa phân nhóm"}</span>
        </div>
      </div>

      {account.golden_windows && account.golden_windows.length > 0 && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs space-y-1">
          <span className="text-semantic-warning font-semibold block">Khung giờ vàng</span>
          <div className="flex flex-wrap gap-1.5">
            {account.golden_windows.map((w, idx) => (
              <span key={`${w}-${idx}`} className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded text-[11px] font-mono">
                {w}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
