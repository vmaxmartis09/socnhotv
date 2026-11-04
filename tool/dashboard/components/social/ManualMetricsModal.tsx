"use client";

import React, { useState } from "react";
import { socialApi } from "@/lib/api/social";
import { useSocialStore } from "@/store/modules/social";
import {
  BarChart3,
  CheckCircle2,
  FileText,
  Upload,
  X,
} from "./icons";

interface ManualMetricsModalProps {
  projectId: string;
}

export function ManualMetricsModal({ projectId }: ManualMetricsModalProps) {
  const {
    posts,
    isManualMetricsModalOpen,
    isImportCsvModalOpen,
    setManualMetricsModalOpen,
    setImportCsvModalOpen,
    loadAnalytics,
  } = useSocialStore();

  const isOpen = isManualMetricsModalOpen || isImportCsvModalOpen;
  const [tab, setTab] = useState<"form" | "csv">(isImportCsvModalOpen ? "csv" : "form");

  // Form state
  const [selectedPostId, setSelectedPostId] = useState("");
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [views, setViews] = useState("1000");
  const [likes, setLikes] = useState("120");
  const [comments, setComments] = useState("15");
  const [shares, setShares] = useState("5");
  const [saves, setSaves] = useState("8");
  const [watchTimeHours, setWatchTimeHours] = useState("12.5");
  const [retentionPct, setRetentionPct] = useState("65");
  const [subscribers, setSubscribers] = useState("25");
  const [revenue, setRevenue] = useState("0");

  // CSV state
  const [csvText, setCsvText] = useState("");
  const [csvPlatform, setCsvPlatform] = useState<"youtube" | "tiktok">("youtube");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleClose = () => {
    setManualMetricsModalOpen(false);
    setImportCsvModalOpen(false);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTargetId) {
      alert("Vui lòng chọn bài viết & mục tiêu cần cập nhật số liệu.");
      return;
    }
    setLoading(true);
    setMsg(null);
    try {
      await socialApi.saveManualMetrics(projectId, {
        post_id: selectedPostId,
        target_id: selectedTargetId,
        views: parseInt(views) || 0,
        likes: parseInt(likes) || 0,
        comments: parseInt(comments) || 0,
        shares: parseInt(shares) || 0,
        saves: parseInt(saves) || 0,
        watch_time_s: (parseFloat(watchTimeHours) || 0) * 3600,
        avg_retention_pct: parseFloat(retentionPct) || 0,
        subscribers_gained: parseInt(subscribers) || 0,
        revenue: parseFloat(revenue) || 0,
      });
      setMsg("Đã lưu số liệu bài viết thành công!");
      await loadAnalytics(projectId);
      setTimeout(() => {
        handleClose();
      }, 1500);
    } catch (err: any) {
      alert("Lỗi: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCsvSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvText.trim()) {
      alert("Vui lòng dán nội dung CSV export từ YouTube Studio hoặc TikTok Studio.");
      return;
    }
    setLoading(true);
    setMsg(null);
    try {
      const res = await socialApi.importCsvMetrics(projectId, csvText, csvPlatform);
      setMsg(`Đã import thành công ${res.total_records} dòng (Khớp ${res.matched_count} bài viết trên hệ thống)!`);
      await loadAnalytics(projectId);
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err: any) {
      alert("Lỗi import CSV: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const currentPost = posts.find((p) => p.id === selectedPostId);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={handleClose}
        />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white dark:bg-zinc-900 rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-xl sm:w-full border border-zinc-200 dark:border-zinc-800">
          {/* Header */}
          <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-zinc-900 dark:text-white">
                  Cập Nhật Số Liệu Bài Viết
                </h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Nhập số liệu thực tế hoặc tải lên tệp CSV xuất từ Studio
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Subtabs */}
          <div className="flex border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-6 pt-2">
            <button
              onClick={() => setTab("form")}
              className={`pb-3 text-sm font-semibold border-b-2 mr-6 transition ${
                tab === "form"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              }`}
            >
              Nhập Thủ Công
            </button>
            <button
              onClick={() => setTab("csv")}
              className={`pb-3 text-sm font-semibold border-b-2 transition ${
                tab === "csv"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              }`}
            >
              Import CSV Studio
            </button>
          </div>

          {/* Alert Message */}
          {msg && (
            <div className="mx-6 mt-4 p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-2 text-sm text-emerald-800 dark:text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              {msg}
            </div>
          )}

          {/* Form Tab */}
          {tab === "form" ? (
            <form onSubmit={handleFormSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                  Chọn Bài Viết
                </label>
                <select
                  value={selectedPostId}
                  onChange={(e) => {
                    const pid = e.target.value;
                    setSelectedPostId(pid);
                    const p = posts.find((item) => item.id === pid);
                    if (p && p.targets.length > 0) {
                      setSelectedTargetId(p.targets[0].id);
                    } else {
                      setSelectedTargetId("");
                    }
                  }}
                  className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  required
                >
                  <option value="">-- Chọn bài viết --</option>
                  {posts.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title} ({p.status})
                    </option>
                  ))}
                </select>
              </div>

              {currentPost && (
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Mục tiêu Nền tảng
                  </label>
                  <select
                    value={selectedTargetId}
                    onChange={(e) => setSelectedTargetId(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                    required
                  >
                    {currentPost.targets.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.platform.toUpperCase()} - {t.account_id} ({t.status})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Lượt xem (Views)
                  </label>
                  <input
                    type="number"
                    value={views}
                    onChange={(e) => setViews(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Lượt thích (Likes)
                  </label>
                  <input
                    type="number"
                    value={likes}
                    onChange={(e) => setLikes(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Bình luận (Comments)
                  </label>
                  <input
                    type="number"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Chia sẻ (Shares)
                  </label>
                  <input
                    type="number"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Thời lượng xem (Giờ)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={watchTimeHours}
                    onChange={(e) => setWatchTimeHours(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                    Tỷ lệ giữ chân (% Retention)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={retentionPct}
                    onChange={(e) => setRetentionPct(e.target.value)}
                    className="w-full text-sm rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-2 text-zinc-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-2 border-t border-zinc-200 dark:border-zinc-800">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition disabled:opacity-50"
                >
                  {loading ? "Đang lưu..." : "Lưu Số Liệu"}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleCsvSubmit} className="p-6 space-y-4">
              <div className="flex items-center gap-4">
                <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  Nền tảng xuất file:
                </span>
                <label className="flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-300 cursor-pointer">
                  <input
                    type="radio"
                    name="csvPlatform"
                    value="youtube"
                    checked={csvPlatform === "youtube"}
                    onChange={() => setCsvPlatform("youtube")}
                  />
                  YouTube Studio
                </label>
                <label className="flex items-center gap-1.5 text-xs text-zinc-700 dark:text-zinc-300 cursor-pointer">
                  <input
                    type="radio"
                    name="csvPlatform"
                    value="tiktok"
                    checked={csvPlatform === "tiktok"}
                    onChange={() => setCsvPlatform("tiktok")}
                  />
                  TikTok Studio
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                  Dán nội dung CSV hoặc kéo tệp vào đây:
                </label>
                <textarea
                  value={csvText}
                  onChange={(e) => setCsvText(e.target.value)}
                  placeholder={`Video title,Video publish time,Views,Watch time (hours),Subscribers\nBài 1,Nov 1,12000,105.2,250\n...`}
                  rows={8}
                  className="w-full text-xs font-mono rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 p-3 text-zinc-900 dark:text-white"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2 border-t border-zinc-200 dark:border-zinc-800">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition disabled:opacity-50 flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  {loading ? "Đang phân tích..." : "Import Số Liệu"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
