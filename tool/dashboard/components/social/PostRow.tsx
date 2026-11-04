"use client";

import React, { useState } from "react";
import { format, parseISO } from "date-fns";
import { vi } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { QueueItem, PlatformType } from "@/lib/api/social";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Copy,
  ExternalLink,
  MoreVertical,
  Play,
  RotateCcw,
  Trash2,
  Upload,
  Video,
} from "./icons";

interface PostRowProps {
  item: QueueItem;
  onOpen: (item: QueueItem) => void;
  onEdit?: (item: QueueItem) => void;
  onReschedule?: (item: QueueItem) => void;
  onDuplicate?: (item: QueueItem) => void;
  onPublishNow?: (item: QueueItem) => void;
  onMarkPublished?: (item: QueueItem) => void;
  onDownloadPackage?: (item: QueueItem) => void;
  onCancel?: (item: QueueItem) => void;
}

const PLATFORM_COLORS: Record<PlatformType, { bg: string; text: string; border: string; label: string }> = {
  youtube: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/20", label: "YouTube" },
  tiktok: { bg: "bg-pink-500/10", text: "text-pink-500", border: "border-pink-500/20", label: "TikTok" },
  facebook: { bg: "bg-blue-600/10", text: "text-blue-600", border: "border-blue-600/20", label: "Facebook" },
  instagram: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/20", label: "Instagram" },
  threads: { bg: "bg-neutral-500/10", text: "text-neutral-400", border: "border-neutral-500/20", label: "Threads" },
  x: { bg: "bg-sky-500/10", text: "text-sky-500", border: "border-sky-500/20", label: "X (Twitter)" },
  douyin: { bg: "bg-amber-500/10", text: "text-amber-500", border: "border-amber-500/20", label: "Douyin" },
};

export function PostRow({
  item,
  onOpen,
  onEdit,
  onReschedule,
  onDuplicate,
  onPublishNow,
  onMarkPublished,
  onDownloadPackage,
  onCancel,
}: PostRowProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const platMeta = PLATFORM_COLORS[item.platform] || {
    bg: "bg-muted",
    text: "text-foreground",
    border: "border-border",
    label: item.platform,
  };

  const formattedTime = item.scheduled_at
    ? (() => {
        try {
          return format(parseISO(item.scheduled_at), "HH:mm, dd/MM", { locale: vi });
        } catch {
          return item.scheduled_at.slice(11, 16);
        }
      })()
    : "Chưa hẹn giờ";

  return (
    <div
      onClick={() => onOpen(item)}
      className="group relative flex items-start gap-2.5 rounded-xl border border-border bg-card p-2.5 transition-all hover:border-primary/40 hover:bg-accent/40 shadow-2xs cursor-pointer select-none"
    >
      {/* Thumbnail or Video Placeholder */}
      <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-muted flex items-center justify-center border border-border/50">
        {item.thumb ? (
          <img
            src={`/api/media?path=${encodeURIComponent(item.thumb)}`}
            alt={item.title}
            className="h-full w-full object-cover"
            onError={(e) => {
              (e.target as HTMLElement).style.display = "none";
            }}
          />
        ) : (
          <Video className="h-5 w-5 text-muted-foreground/60" />
        )}
      </div>

      {/* Main Details */}
      <div className="min-w-0 flex-1 space-y-1">
        {/* Title: 2 lines with full tooltip */}
        <p
          title={item.title}
          className="text-xs font-semibold leading-snug text-foreground line-clamp-2 group-hover:text-primary transition-colors"
        >
          {item.title}
        </p>

        {/* Badges Row */}
        <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
          {/* Full Platform Chip */}
          <span
            className={cn(
              "inline-flex items-center rounded-md px-1.5 py-0.5 font-medium border",
              platMeta.bg,
              platMeta.text,
              platMeta.border
            )}
          >
            {platMeta.label}
          </span>

          {/* Account Name */}
          <span className="font-medium text-foreground truncate max-w-[110px]" title={item.account_name}>
            {item.account_name}
          </span>

          {/* Scheduled Time */}
          <span className="flex items-center gap-0.5 text-muted-foreground font-mono">
            <Clock className="h-3 w-3" />
            {formattedTime}
          </span>

          {/* Status Badge */}
          {item.bucket === "overdue" && (
            <span className="rounded-md bg-amber-500/10 px-1.5 py-0.5 font-semibold text-amber-500 border border-amber-500/20">
              Quá hạn
            </span>
          )}
          {item.status === "pending_approval" && item.bucket !== "overdue" && (
            <span className="rounded-md bg-amber-500/10 px-1.5 py-0.5 font-semibold text-amber-500 border border-amber-500/20">
              Chờ duyệt
            </span>
          )}
          {item.status === "scheduled" && item.bucket !== "overdue" && (
            <span className="rounded-md bg-indigo-500/10 px-1.5 py-0.5 font-semibold text-indigo-400 border border-indigo-500/20">
              Đã lên lịch
            </span>
          )}
          {item.status === "published" && (
            <span className="rounded-md bg-emerald-500/10 px-1.5 py-0.5 font-semibold text-emerald-500 border border-emerald-500/20 flex items-center gap-0.5">
              <CheckCircle2 className="h-3 w-3" />
              Đã đăng
            </span>
          )}
          {item.status === "failed" && (
            <span className="rounded-md bg-rose-500/10 px-1.5 py-0.5 font-semibold text-rose-500 border border-rose-500/20">
              Lỗi
            </span>
          )}

          {/* Issues Indicator */}
          {item.issues && item.issues.length > 0 && (
            <span
              title={item.issues.map((i) => i.message_vi).join("\n")}
              className="inline-flex items-center text-amber-500"
            >
              <AlertTriangle className="h-3 w-3" />
            </span>
          )}
        </div>
      </div>

      {/* Action Menu (Three dots) */}
      <div className="relative shrink-0" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          onClick={() => setMenuOpen(!menuOpen)}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          title="Tùy chọn bài viết"
        >
          <MoreVertical className="h-4 w-4" />
        </button>

        {menuOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-8 z-50 w-48 rounded-xl border border-border bg-popover p-1 text-xs shadow-xl animate-in fade-in-50 zoom-in-95">
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onEdit ? onEdit(item) : onOpen(item);
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-foreground hover:bg-accent transition-colors"
              >
                <span>Sửa bài viết</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onReschedule && onReschedule(item);
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-foreground hover:bg-accent transition-colors"
              >
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Đổi giờ đăng</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onDuplicate && onDuplicate(item);
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-foreground hover:bg-accent transition-colors"
              >
                <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Nhân bản sang kênh khác</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (confirm(`Xác nhận đăng bài "${item.title}" lên ${item.account_name} ngay bây giờ?`)) {
                    onPublishNow && onPublishNow(item);
                  }
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left font-medium text-emerald-500 hover:bg-emerald-500/10 transition-colors"
              >
                <Play className="h-3.5 w-3.5" />
                <span>Đăng ngay (Xác nhận)</span>
              </button>

              {item.is_manual && (
                <>
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      onMarkPublished && onMarkPublished(item);
                    }}
                    className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-foreground hover:bg-accent transition-colors"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    <span>Tôi đã đăng</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      onDownloadPackage && onDownloadPackage(item);
                    }}
                    className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-foreground hover:bg-accent transition-colors"
                  >
                    <Upload className="h-3.5 w-3.5 text-primary" />
                    <span>Tải gói đăng tay (.zip)</span>
                  </button>
                </>
              )}

              <div className="my-1 border-t border-border/50" />

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (confirm(`Hủy lịch đăng bài "${item.title}" trên ${item.account_name}?`)) {
                    onCancel && onCancel(item);
                  }
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left font-medium text-rose-500 hover:bg-rose-500/10 transition-colors"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Huỷ lịch đăng</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
