"use client";

import React, { useState, useMemo } from "react";
import { format, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { PlatformType, Post, PostStatus, socialApi } from "@/lib/api/social";
import {
  Copy,
  Film,
  Pencil,
  Search,
  Trash2,
  X,
  Check,
  RotateCcw,
} from "@/components/ui/icons";

interface PostsTabProps {
  projectId: string;
}

const STATUS_BADGES: Record<PostStatus, { label: string; className: string }> = {
  draft: { label: "Bản nháp", className: "bg-muted text-muted-foreground border-border" },
  pending_approval: { label: "Chờ duyệt", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20" },
  approved: { label: "Đã duyệt", className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20" },
  scheduled: { label: "Đã lên lịch", className: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20" },
  publishing: { label: "Đang đăng", className: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20 animate-pulse" },
  published: { label: "Đã đăng", className: "bg-green-600/10 text-green-700 dark:text-green-400 border-green-600/20" },
  failed: { label: "Thất bại", className: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20" },
  cancelled: { label: "Đã huỷ", className: "bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20" },
};

export function PostsTab({ projectId }: PostsTabProps) {
  const { posts, loadPosts, openComposer } = useSocialStore();
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState<PlatformType | "all">("all");
  const [statusFilter, setStatusFilter] = useState<PostStatus | "all">("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const filteredPosts = useMemo(() => {
    return posts.filter((p) => {
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (platformFilter !== "all" && !p.targets.some((t) => t.platform === platformFilter))
        return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchTitle = p.title.toLowerCase().includes(q);
        const matchCaption = p.targets.some((t) => t.caption.toLowerCase().includes(q));
        if (!matchTitle && !matchCaption) return false;
      }
      return true;
    });
  }, [posts, statusFilter, platformFilter, search]);

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const selectAll = () => {
    if (selectedIds.size === filteredPosts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredPosts.map((p) => p.id)));
    }
  };

  const handleDuplicate = async (postId: string) => {
    try {
      await socialApi.duplicatePost(projectId, postId);
      await loadPosts(projectId);
    } catch (e: any) {
      alert(`Lỗi nhân bản: ${e.message}`);
    }
  };

  const handleCancel = async (postId: string) => {
    try {
      await socialApi.cancelPost(projectId, postId);
      await loadPosts(projectId);
    } catch (e: any) {
      alert(`Lỗi huỷ bài: ${e.message}`);
    }
  };

  const handleDelete = async (postId: string) => {
    if (!window.confirm("Bạn có chắc muốn xoá bài viết này?")) return;
    try {
      await socialApi.deletePost(projectId, postId);
      await loadPosts(projectId);
    } catch (e: any) {
      alert(`Lỗi xoá: ${e.message}`);
    }
  };

  const handleBulkAction = async (action: "approve" | "duplicate" | "cancel" | "delete") => {
    if (selectedIds.size === 0) return;
    const count = selectedIds.size;
    if (
      action === "delete" &&
      !window.confirm(`Bạn có chắc muốn xoá ${count} bài viết đã chọn?`)
    ) {
      return;
    }

    for (const pid of Array.from(selectedIds)) {
      try {
        if (action === "approve") await socialApi.approvePost(projectId, pid);
        else if (action === "duplicate") await socialApi.duplicatePost(projectId, pid);
        else if (action === "cancel") await socialApi.cancelPost(projectId, pid);
        else if (action === "delete") await socialApi.deletePost(projectId, pid);
      } catch {}
    }
    setSelectedIds(new Set());
    await loadPosts(projectId);
  };

  return (
    <div className="space-y-4">
      {/* Search & Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-2xs">
        <div className="flex flex-1 items-center gap-2 max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm kiếm bài viết, caption..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-border bg-background py-1.5 pl-8 pr-3 text-xs placeholder:text-muted-foreground focus:ring-1 focus:ring-primary focus:outline-hidden"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {/* Platform Filter */}
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value as any)}
            className="rounded-lg border border-border bg-background px-2.5 py-1.5 font-medium text-foreground focus:outline-hidden"
          >
            <option value="all">Tất cả nền tảng</option>
            <option value="youtube">YouTube</option>
            <option value="tiktok">TikTok</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
            <option value="douyin">Douyin</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="rounded-lg border border-border bg-background px-2.5 py-1.5 font-medium text-foreground focus:outline-hidden"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="draft">Bản nháp</option>
            <option value="pending_approval">Chờ duyệt</option>
            <option value="approved">Đã duyệt</option>
            <option value="scheduled">Đã lên lịch</option>
            <option value="publishing">Đang đăng</option>
            <option value="published">Đã đăng</option>
            <option value="failed">Thất bại</option>
            <option value="cancelled">Đã huỷ</option>
          </select>
        </div>
      </div>

      {/* Selected Items Bulk Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center justify-between rounded-lg border border-primary/40 bg-primary/10 px-4 py-2 text-xs font-semibold text-primary">
          <span>Đã chọn {selectedIds.size} bài viết</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleBulkAction("approve")}
              className="flex items-center gap-1 rounded bg-emerald-600 px-2 py-1 text-white hover:bg-emerald-700"
            >
              <Check className="h-3.5 w-3.5" />
              Duyệt
            </button>
            <button
              onClick={() => handleBulkAction("duplicate")}
              className="flex items-center gap-1 rounded bg-background px-2 py-1 text-foreground border border-border hover:bg-muted"
            >
              <Copy className="h-3.5 w-3.5" />
              Nhân bản
            </button>
            <button
              onClick={() => handleBulkAction("cancel")}
              className="flex items-center gap-1 rounded bg-background px-2 py-1 text-foreground border border-border hover:bg-muted"
            >
              <X className="h-3.5 w-3.5" />
              Huỷ
            </button>
            <button
              onClick={() => handleBulkAction("delete")}
              className="flex items-center gap-1 rounded bg-rose-600 px-2 py-1 text-white hover:bg-rose-700"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Xoá
            </button>
          </div>
        </div>
      )}

      {/* Posts Table */}
      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-2xs">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border bg-muted/40 font-semibold uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="p-3 w-8">
                <input
                  type="checkbox"
                  checked={
                    filteredPosts.length > 0 &&
                    selectedIds.size === filteredPosts.length
                  }
                  onChange={selectAll}
                  className="rounded border-border"
                />
              </th>
              <th className="p-3">Bài viết & Video</th>
              <th className="p-3">Nền tảng & Kênh</th>
              <th className="p-3">Thời gian</th>
              <th className="p-3">Trạng thái</th>
              <th className="p-3 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredPosts.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  Không tìm thấy bài viết nào phù hợp.
                </td>
              </tr>
            ) : (
              filteredPosts.map((post) => {
                const media = post.media[0];
                const badge = STATUS_BADGES[post.status] || STATUS_BADGES.draft;

                return (
                  <tr
                    key={post.id}
                    className="group hover:bg-muted/30 transition-colors cursor-pointer"
                    onClick={() => openComposer(post)}
                  >
                    <td className="p-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(post.id)}
                        onChange={() => toggleSelect(post.id)}
                        className="rounded border-border"
                      />
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-3">
                        {media?.thumb ? (
                          <img
                            src={media.thumb}
                            alt=""
                            className="h-10 w-10 rounded-md object-cover border border-border shrink-0"
                          />
                        ) : (
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
                            <Film className="h-5 w-5 opacity-50" />
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="font-semibold text-foreground line-clamp-1">
                            {post.title}
                          </p>
                          <p className="text-[11px] text-muted-foreground line-clamp-1">
                            {post.targets[0]?.caption || "(Chưa có caption)"}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {post.targets.map((t) => (
                          <span
                            key={t.id}
                            className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-foreground"
                          >
                            {t.platform}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3 font-mono text-[11px] text-muted-foreground">
                      {post.targets[0]?.scheduled_at
                        ? format(parseISO(post.targets[0].scheduled_at), "HH:mm dd/MM/yyyy")
                        : format(parseISO(post.created_at), "dd/MM/yyyy")}
                    </td>
                    <td className="p-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold",
                          badge.className
                        )}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openComposer(post)}
                          title="Chỉnh sửa bài"
                          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDuplicate(post.id)}
                          title="Nhân bản bài"
                          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleCancel(post.id)}
                          title="Huỷ bài"
                          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-rose-500"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(post.id)}
                          title="Xoá vĩnh viễn"
                          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-rose-600"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
