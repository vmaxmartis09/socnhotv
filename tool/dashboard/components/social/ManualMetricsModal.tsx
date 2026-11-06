"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { socialApi } from "@/lib/api/social";
import {
  X,
  Sparkles,
  FileText,
  Upload,
  CheckCircle,
  AlertCircle,
  RefreshCw,
} from "@/components/ui/icons";

interface ManualMetricsModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  targets: Array<{
    target_id: string;
    post_id: string;
    title: string;
    platform: string;
  }>;
  onSuccess?: () => void;
}

export function ManualMetricsModal({
  isOpen,
  onClose,
  projectId,
  targets,
  onSuccess,
}: ManualMetricsModalProps) {
  const [activeTab, setActiveTab] = useState<"manual" | "csv">("manual");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Manual Form State
  const [selectedTargetId, setSelectedTargetId] = useState(targets[0]?.target_id || "");
  const [views, setViews] = useState<number>(0);
  const [retentionPct, setRetentionPct] = useState<number>(0);
  const [likes, setLikes] = useState<number>(0);
  const [comments, setComments] = useState<number>(0);
  const [shares, setShares] = useState<number>(0);
  const [watchTimeS, setWatchTimeS] = useState<number>(0);

  // CSV Form State
  const [csvPlatform, setCsvPlatform] = useState("youtube");
  const [csvText, setCsvText] = useState("");

  if (!isOpen) return null;

  const currentTarget = targets.find((t) => t.target_id === selectedTargetId) || targets[0];

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentTarget) {
      setErrorMsg("Chưa chọn bài viết đích");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await socialApi.saveManualMetrics(projectId, {
        post_id: currentTarget.post_id,
        target_id: currentTarget.target_id,
        platform: currentTarget.platform,
        views: Number(views),
        avg_retention_pct: Number(retentionPct),
        likes: Number(likes),
        comments: Number(comments),
        shares: Number(shares),
        watch_time_s: Number(watchTimeS),
      });

      // Automatically generate updated insights & recommendations
      await socialApi.generateInsights(projectId);

      setSuccessMsg("Đã lưu số liệu và sinh bộ gợi ý mới cho tập sau!");
      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1200);
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi lưu số liệu");
    } finally {
      setLoading(false);
    }
  };

  const handleCsvSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvText.trim()) {
      setErrorMsg("Vui lòng dán nội dung CSV");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await socialApi.importCsvMetrics(projectId, csvText.trim(), csvPlatform);
      await socialApi.generateInsights(projectId);

      setSuccessMsg(
        `Đã nhập thành công ${res.total_records} dòng (${res.matched_count} bài khớp) và cập nhật gợi ý tập sau!`
      );
      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi nhập CSV");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-lg max-h-[90vh] flex flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden text-xs">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-muted/40">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-foreground text-sm leading-tight">
                Nhập Số Liệu & Tự Học Cho Tập Sau
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Nhập lượt xem, giữ chân bằng tay hoặc CSV để sinh gợi ý kịch bản
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Đóng"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-border bg-muted/20 px-5 pt-2 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("manual")}
            className={cn(
              "pb-2 px-3 font-semibold text-xs border-b-2 transition-colors",
              activeTab === "manual"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            Nhập tay từng bài
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("csv")}
            className={cn(
              "pb-2 px-3 font-semibold text-xs border-b-2 transition-colors",
              activeTab === "csv"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            Nhập file CSV (YouTube / TikTok)
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 scroll-quiet">
          {errorMsg && (
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 text-xs">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-xs">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {activeTab === "manual" ? (
            <form onSubmit={handleManualSubmit} className="space-y-3.5">
              {/* Target selector */}
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground block text-[11px]">
                  Chọn bài viết / Kênh
                </label>
                <select
                  value={selectedTargetId}
                  onChange={(e) => setSelectedTargetId(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {targets.map((t) => (
                    <option key={t.target_id} value={t.target_id}>
                      [{t.platform.toUpperCase()}] {t.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Views & Retention */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Lượt xem (Views)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={views || ""}
                    onChange={(e) => setViews(Number(e.target.value))}
                    placeholder="VD: 5200"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Tỷ lệ giữ chân (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={retentionPct || ""}
                    onChange={(e) => setRetentionPct(Number(e.target.value))}
                    placeholder="VD: 62.5"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                    required
                  />
                </div>
              </div>

              {/* Likes & Comments */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Lượt thích (Likes)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={likes || ""}
                    onChange={(e) => setLikes(Number(e.target.value))}
                    placeholder="VD: 340"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Bình luận (Comments)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={comments || ""}
                    onChange={(e) => setComments(Number(e.target.value))}
                    placeholder="VD: 45"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>
              </div>

              {/* Shares & Watch time */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Chia sẻ (Shares)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={shares || ""}
                    onChange={(e) => setShares(Number(e.target.value))}
                    placeholder="VD: 20"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground block text-[11px]">
                    Thời gian xem tích lũy (giây)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={watchTimeS || ""}
                    onChange={(e) => setWatchTimeS(Number(e.target.value))}
                    placeholder="VD: 15600"
                    className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Đang lưu và sinh gợi ý...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Lưu số liệu & Cập nhật gợi ý tập sau</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleCsvSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground block text-[11px]">
                  Nền tảng xuất file CSV
                </label>
                <select
                  value={csvPlatform}
                  onChange={(e) => setCsvPlatform(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="youtube">YouTube Studio CSV</option>
                  <option value="tiktok">TikTok Analytics CSV</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground block text-[11px]">
                  Dán nội dung CSV (hoặc kéo thả văn bản)
                </label>
                <textarea
                  rows={6}
                  value={csvText}
                  onChange={(e) => setCsvText(e.target.value)}
                  placeholder={`Video title,Views,Watch time (hours),Average percentage viewed (%),Likes,Comments\nTập 1: Núi Lửa Trong Bụng Bi,12500,85.2,64.8,820,115\nTập 2: Mun Sợ Bóng Tối,8400,52.1,58.3,510,74`}
                  className="w-full p-3 rounded-lg border border-border bg-background text-foreground font-mono text-[11px] focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed"
                  required
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Đang nạp CSV và sinh gợi ý...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      <span>Nhập CSV & Tự động sinh gợi ý tập sau</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
