"use client";

import React, { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Grid,
  List,
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Plus,
  RefreshCw,
  Film,
  Calendar,
} from "@/components/ui/icons";
import { VideoThumb } from "../common/VideoThumb";
import { StatusBadge } from "../common/StatusBadge";
import { AccountChip } from "../common/AccountChip";
import { LibraryVideo } from "@/lib/api/social";

interface VideoLibraryViewProps {
  onPlanVideos: (videoIds: string[]) => void;
}

export function VideoLibraryView({ onPlanVideos }: VideoLibraryViewProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const {
    libraryVideos,
    loadLibrary,
    loading: isLoadingLibrary,
    accounts,
    setHubSelectedEntity,
    hubSelectedEntity,
  } = useSocialStore();

  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [accountFilter, setAccountFilter] = useState<string>("all");
  const [selectedVideoIds, setSelectedVideoIds] = useState<string[]>([]);

  useEffect(() => {
    if (activeProjectId) {
      loadLibrary(activeProjectId);
    }
  }, [activeProjectId, loadLibrary]);

  // Filter videos locally or trigger refetch
  const filteredVideos = useMemo(() => {
    return libraryVideos.filter((vid) => {
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = vid.title.toLowerCase().includes(q);
        const matchesId = vid.id.toLowerCase().includes(q);
        if (!matchesTitle && !matchesId) return false;
      }

      // Status filter
      if (statusFilter !== "all") {
        const posts = vid.posts_by_account || [];
        if (statusFilter === "unposted") {
          // Has no posts or all posts are unposted
          const hasAnyPost = posts.some((p) => p.status !== "unposted");
          if (hasAnyPost) return false;
        } else if (statusFilter === "scheduled") {
          const hasScheduled = posts.some((p) => p.status === "scheduled");
          if (!hasScheduled) return false;
        } else if (statusFilter === "published") {
          const hasPublished = posts.some((p) => p.status === "published");
          if (!hasPublished) return false;
        }
      }

      // Account filter
      if (accountFilter !== "all") {
        const post = vid.posts_by_account?.find((p) => p.account_id === accountFilter);
        if (!post) return false;
      }

      return true;
    });
  }, [libraryVideos, searchQuery, statusFilter, accountFilter]);

  const handleToggleSelect = (videoId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedVideoIds((prev) =>
      prev.includes(videoId) ? prev.filter((id) => id !== videoId) : [...prev, videoId]
    );
  };

  const handleSelectAll = () => {
    if (selectedVideoIds.length === filteredVideos.length) {
      setSelectedVideoIds([]);
    } else {
      setSelectedVideoIds(filteredVideos.map((v) => v.id));
    }
  };

  const handleSelectVideo = (video: LibraryVideo) => {
    setHubSelectedEntity({
      type: "video",
      id: video.id,
      data: video,
    });
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Top Controls Bar */}
      <div className="p-4 border-b border-border bg-card/60 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2 flex-1 min-w-[240px] max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm kiếm video theo tên, ID... (Phím /)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground focus:outline-none"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="unposted">Chưa đăng ở đâu</option>
            <option value="scheduled">Đang có lịch hẹn</option>
            <option value="published">Đã xuất bản</option>
          </select>

          {/* Account Filter */}
          <select
            value={accountFilter}
            onChange={(e) => setAccountFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-background border border-border text-xs text-foreground focus:outline-none"
          >
            <option value="all">Tất cả tài khoản</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.display_name} ({acc.platform})
              </option>
            ))}
          </select>

          {/* View Mode Toggle */}
          <div className="flex items-center border border-border rounded-lg p-0.5 bg-background">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={cn(
                "p-1.5 rounded text-xs",
                viewMode === "grid" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
              aria-label="Xem dạng lưới"
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={cn(
                "p-1.5 rounded text-xs",
                viewMode === "table" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
              aria-label="Xem dạng bảng"
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            type="button"
            onClick={() => activeProjectId && loadLibrary(activeProjectId)}
            className="p-1.5 rounded-lg border border-border bg-background text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Tải lại kho video"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isLoadingLibrary && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Floating Bulk Selection Action Bar */}
      {selectedVideoIds.length > 0 && (
        <div className="bg-primary/10 border-b border-primary/20 px-4 py-2.5 flex items-center justify-between shrink-0 animate-in fade-in slide-in-from-top-1">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={selectedVideoIds.length === filteredVideos.length && filteredVideos.length > 0}
              onChange={handleSelectAll}
              className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
            />
            <span className="text-xs font-semibold text-primary">
              Đã chọn {selectedVideoIds.length} / {filteredVideos.length} video
            </span>
            <button
              type="button"
              onClick={() => setSelectedVideoIds([])}
              className="text-xs text-muted-foreground hover:underline ml-2"
            >
              Bỏ chọn
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onPlanVideos(selectedVideoIds)}
              className="px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground font-medium text-xs flex items-center gap-1.5 hover:bg-primary/90 transition-colors shadow-sm"
            >
              <Calendar className="w-3.5 h-3.5" />
              Đăng các video đã chọn ({selectedVideoIds.length})
            </button>
          </div>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 scroll-quiet">
        {isLoadingLibrary && libraryVideos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <RefreshCw className="w-8 h-8 animate-spin mb-3 text-primary" />
            <p className="text-xs">Đang quét kho video thành phẩm...</p>
          </div>
        ) : filteredVideos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center border-2 border-dashed border-border rounded-xl p-6">
            <Film className="w-10 h-10 text-muted-foreground mb-3" />
            <h3 className="text-sm font-semibold text-foreground">Không tìm thấy video nào</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm">
              Không có video nào khớp với bộ lọc hoặc dự án chưa xuất bản video nào vào kho.
            </p>
          </div>
        ) : viewMode === "grid" ? (
          /* Grid View */
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredVideos.map((video) => {
              const isSelected = selectedVideoIds.includes(video.id);
              const isEntityActive = hubSelectedEntity?.id === video.id || (hubSelectedEntity?.data as any)?.id === video.id;

              return (
                <div
                  key={video.id}
                  onClick={() => handleSelectVideo(video)}
                  className={cn(
                    "virtual-card group relative flex flex-col rounded-xl border bg-card overflow-hidden cursor-pointer transition-all hover:shadow-md",
                    isEntityActive
                      ? "border-primary ring-1 ring-primary"
                      : "border-border hover:border-border/80",
                    isSelected && "bg-primary/5"
                  )}
                >
                  {/* Select Checkbox */}
                  <div
                    onClick={(e) => handleToggleSelect(video.id, e)}
                    className="absolute top-2 left-2 z-10 w-6 h-6 rounded-md bg-black/60 backdrop-blur-sm flex items-center justify-center cursor-pointer border border-white/20 hover:scale-105 transition-transform"
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="rounded border-white/40 text-primary focus:ring-0 w-3.5 h-3.5 pointer-events-none"
                    />
                  </div>

                  {/* Thumbnail */}
                  <VideoThumb
                    thumb={video.thumb}
                    title={video.title}
                    durationSec={video.duration_s || video.duration_sec}
                    aspectRatio={video.aspect_ratio}
                    className="w-full h-44"
                  />

                  {/* Meta */}
                  <div className="p-3 flex-1 flex flex-col justify-between space-y-3">
                    <div>
                      <h4 className="text-xs font-semibold text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                        {video.title}
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5 font-mono truncate">
                        {video.id}
                      </p>
                    </div>

                    {/* Per-Account Status Chips */}
                    <div className="space-y-1.5 border-t border-border/50 pt-2">
                      <div className="text-[10px] uppercase font-semibold tracking-wider text-muted-foreground">
                        Tài khoản
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {accounts.map((acc) => {
                          const p = video.posts_by_account?.find((item) => item.account_id === acc.id);
                          const status = p?.status || "unposted";

                          return (
                            <span
                              key={acc.id}
                              title={`${acc.display_name}: ${status}`}
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-muted/60 border border-border/40"
                            >
                              <span className="font-semibold">{acc.platform.slice(0, 2).toUpperCase()}</span>
                              <span>
                                {status === "published"
                                  ? "✅"
                                  : status === "scheduled"
                                  ? "🕒"
                                  : status === "failed"
                                  ? "⚠️"
                                  : "⚪"}
                              </span>
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Table View */
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-muted-foreground">
                  <th className="p-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={selectedVideoIds.length === filteredVideos.length && filteredVideos.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-border text-primary focus:ring-primary w-3.5 h-3.5 cursor-pointer"
                    />
                  </th>
                  <th className="p-3 font-semibold w-16">Xem</th>
                  <th className="p-3 font-semibold">Tên Video</th>
                  <th className="p-3 font-semibold w-24">Thời lượng</th>
                  <th className="p-3 font-semibold w-20">Tỉ lệ</th>
                  <th className="p-3 font-semibold">Trạng thái theo Tài khoản</th>
                  <th className="p-3 font-semibold w-24 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredVideos.map((video) => {
                  const isSelected = selectedVideoIds.includes(video.id);
                  const isEntityActive = hubSelectedEntity?.id === video.id || (hubSelectedEntity?.data as any)?.id === video.id;

                  return (
                    <tr
                      key={video.id}
                      onClick={() => handleSelectVideo(video)}
                      className={cn(
                        "virtual-row hover:bg-muted/40 cursor-pointer transition-colors",
                        isEntityActive && "bg-muted/60",
                        isSelected && "bg-primary/5"
                      )}
                    >
                      <td className="p-3 text-center" onClick={(e) => handleToggleSelect(video.id, e)}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="rounded border-border text-primary focus:ring-primary w-3.5 h-3.5 cursor-pointer"
                        />
                      </td>
                      <td className="p-2">
                        <VideoThumb
                          thumb={video.thumb}
                          title={video.title}
                          className="w-14 h-9 rounded"
                        />
                      </td>
                      <td className="p-3 font-medium text-foreground">
                        <div className="font-semibold">{video.title}</div>
                        <div className="text-[11px] text-muted-foreground font-mono truncate max-w-xs">
                          {video.id}
                        </div>
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {(video.duration_s || video.duration_sec) ? `${Math.round(video.duration_s || video.duration_sec!)}s` : "-"}
                      </td>
                      <td className="p-3 text-muted-foreground">{video.aspect_ratio || "9:16"}</td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1.5">
                          {accounts.map((acc) => {
                            const p = video.posts_by_account?.find((item) => item.account_id === acc.id);
                            const status = p?.status || "unposted";

                            return (
                              <span
                                key={acc.id}
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-muted/60 border border-border/40"
                              >
                                <span>{acc.platform.slice(0, 2).toUpperCase()}</span>
                                <StatusBadge status={status} size="sm" />
                              </span>
                            );
                          })}
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onPlanVideos([video.id]);
                          }}
                          className="px-2.5 py-1 rounded bg-primary/10 hover:bg-primary/20 text-primary text-[11px] font-medium transition-colors"
                        >
                          Đăng
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
