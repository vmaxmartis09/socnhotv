"use client";

import React, { useEffect, useState } from "react";
import { useSocialStore } from "@/store/modules/social";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  DollarSign,
  Eye,
  FileText,
  Flame,
  RefreshCw,
  Sparkles,
  ThumbsUp,
  TrendingUp,
  Upload,
  Users,
  Zap,
} from "./icons";
import { ManualMetricsModal } from "./ManualMetricsModal";
import { AutomationRulesModal } from "./AutomationRulesModal";

interface AnalyticsTabProps {
  projectId: string;
}

export function AnalyticsTab({ projectId }: AnalyticsTabProps) {
  const {
    analyticsOverview,
    heatmapData,
    creativesData,
    learningsData,
    loadAnalytics,
    loadHeatmap,
    applyGoldenWindows,
    loadCreatives,
    loadLearnings,
    triggerAnalyticsCollect,
    setManualMetricsModalOpen,
    setImportCsvModalOpen,
    setAutomationModalOpen,
  } = useSocialStore();

  const [windowFilter, setWindowFilter] = useState("30d");
  const [refreshing, setRefreshing] = useState(false);
  const [applyingWindows, setApplyingWindows] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(false);
  const [hoveredSlot, setHoveredSlot] = useState<{
    weekday: number;
    hour: number;
    views: number;
    count: number;
    score: number;
  } | null>(null);

  useEffect(() => {
    loadAnalytics(projectId, windowFilter);
    loadHeatmap(projectId);
    loadCreatives(projectId);
    loadLearnings(projectId);
  }, [projectId, windowFilter]);

  const handleRefreshCollect = async () => {
    setRefreshing(true);
    try {
      await triggerAnalyticsCollect(projectId);
      await loadHeatmap(projectId);
      await loadCreatives(projectId);
      await loadLearnings(projectId);
    } catch (e: any) {
      alert("Lỗi thu thập: " + e.message);
    } finally {
      setRefreshing(false);
    }
  };

  const handleApplyGolden = async () => {
    setApplyingWindows(true);
    setAppliedSuccess(false);
    try {
      await applyGoldenWindows(projectId);
      setAppliedSuccess(true);
      setTimeout(() => setAppliedSuccess(false), 3000);
    } catch (e: any) {
      alert("Lỗi: " + e.message);
    } finally {
      setApplyingWindows(false);
    }
  };

  const kpis = analyticsOverview?.kpis;
  const viewsByDay = analyticsOverview?.views_by_day || {};
  const dayKeys = Object.keys(viewsByDay).sort();

  // Prepare SVG chart points for views_by_day
  const maxDayViews = Math.max(
    ...dayKeys.map((d) => viewsByDay[d]?.total || 0),
    100
  );
  const chartHeight = 160;
  const chartWidth = 700;

  const getPoints = (key: string) => {
    if (dayKeys.length === 0) return "";
    return dayKeys
      .map((d, i) => {
        const x = (i / (dayKeys.length - 1)) * (chartWidth - 40) + 20;
        const v = key === "total" ? viewsByDay[d]?.total || 0 : viewsByDay[d]?.[key] || 0;
        const y = chartHeight - (v / maxDayViews) * (chartHeight - 30) - 15;
        return `${x},${y}`;
      })
      .join(" ");
  };

  const weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"];

  // Heatmap intensity helper
  const getSlotColor = (score: number) => {
    if (score <= 10) return "bg-zinc-100 dark:bg-zinc-800/60";
    if (score < 40) return "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300";
    if (score < 80) return "bg-emerald-300 dark:bg-emerald-800 text-emerald-950 dark:text-emerald-100";
    if (score < 150) return "bg-emerald-400 dark:bg-emerald-600 text-white font-bold";
    return "bg-emerald-500 dark:bg-emerald-500 text-white font-bold shadow-sm";
  };

  return (
    <div className="space-y-6">
      {/* Modals */}
      <ManualMetricsModal projectId={projectId} />
      <AutomationRulesModal projectId={projectId} />

      {/* Top Controls Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-900 dark:text-white">
              Báo Cáo Phân Tích & Giờ Vàng
            </h2>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Chỉ số tăng trưởng đa nền tảng, giờ vàng tối ưu và vòng lặp tự học nội dung
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Time range selector */}
          <div className="flex rounded-xl bg-zinc-100 dark:bg-zinc-800 p-1">
            {["7d", "30d", "all"].map((w) => (
              <button
                key={w}
                onClick={() => setWindowFilter(w)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  windowFilter === w
                    ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-sm"
                    : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
                }`}
              >
                {w === "7d" ? "7 ngày" : w === "30d" ? "30 ngày" : "Tất cả"}
              </button>
            ))}
          </div>

          <button
            onClick={() => setManualMetricsModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Nhập số liệu
          </button>

          <button
            onClick={() => setImportCsvModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition"
          >
            <Upload className="w-3.5 h-3.5" />
            Import CSV
          </button>

          <button
            onClick={handleRefreshCollect}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Thu thập mới
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
            <span className="text-xs font-medium">Tổng Lượt Xem</span>
            <Eye className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-zinc-900 dark:text-white">
            {kpis ? (kpis.total_views > 1000 ? `${(kpis.total_views / 1000).toFixed(1)}K` : kpis.total_views) : "--"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {kpis?.post_count || 0} bài đã xuất bản
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
            <span className="text-xs font-medium">Tỷ Lệ Tương Tác</span>
            <ThumbsUp className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {kpis ? `${kpis.engagement_rate}%` : "--"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            ER = (like+cmt+share)/views
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
            <span className="text-xs font-medium">Thời Lượng Xem</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-zinc-900 dark:text-white">
            {kpis ? `${(kpis.total_watch_time_s / 3600).toFixed(1)}h` : "--"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            Giữ chân TB: {kpis?.avg_retention_pct || 0}%
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
            <span className="text-xs font-medium">Follower Mới</span>
            <Users className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="text-2xl font-black text-cyan-600 dark:text-cyan-400">
            {kpis ? `+${kpis.follower_gain}` : "--"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            Thu hút qua video
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
            <span className="text-xs font-medium">Doanh Thu Affiliate</span>
            <DollarSign className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400">
            {kpis ? `$${kpis.affiliate_revenue}` : "--"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            CTR sản phẩm: {kpis?.avg_ctr || 0}%
          </div>
        </div>
      </div>

      {/* SVG Views Trend Chart */}
      <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-sm text-zinc-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-500" />
              Biểu Đồ Lượt Xem Theo Ngày
            </h3>
            <p className="text-xs text-zinc-400">
              Tổng lượt xem video 14 ngày gần nhất
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
              <span className="text-zinc-600 dark:text-zinc-400">Tổng Views</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-zinc-600 dark:text-zinc-400">TikTok</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span className="text-zinc-600 dark:text-zinc-400">YouTube</span>
            </div>
          </div>
        </div>

        <div className="w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            className="w-full h-44 text-zinc-300 dark:text-zinc-700"
          >
            {/* Horizontal Grid lines */}
            <line x1="20" y1="15" x2={chartWidth - 20} y2="15" stroke="currentColor" strokeDasharray="3 3" strokeOpacity="0.4" />
            <line x1="20" y1={chartHeight / 2} x2={chartWidth - 20} y2={chartHeight / 2} stroke="currentColor" strokeDasharray="3 3" strokeOpacity="0.4" />
            <line x1="20" y1={chartHeight - 15} x2={chartWidth - 20} y2={chartHeight - 15} stroke="currentColor" strokeOpacity="0.6" />

            {/* Total Line */}
            {dayKeys.length > 1 && (
              <polyline
                fill="none"
                stroke="#6366f1"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={getPoints("total")}
              />
            )}

            {/* TikTok Line */}
            {dayKeys.length > 1 && (
              <polyline
                fill="none"
                stroke="#22d3ee"
                strokeWidth="2"
                strokeDasharray="4 4"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={getPoints("tiktok")}
              />
            )}

            {/* YouTube Line */}
            {dayKeys.length > 1 && (
              <polyline
                fill="none"
                stroke="#f43f5e"
                strokeWidth="2"
                strokeDasharray="4 4"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={getPoints("youtube")}
              />
            )}

            {/* Data dots on Total Line */}
            {dayKeys.map((d, i) => {
              const x = (i / (dayKeys.length - 1)) * (chartWidth - 40) + 20;
              const v = viewsByDay[d]?.total || 0;
              const y = chartHeight - (v / maxDayViews) * (chartHeight - 30) - 15;
              return (
                <g key={d} className="group cursor-pointer">
                  <circle cx={x} cy={y} r="4" fill="#6366f1" className="transition-transform group-hover:r-6" />
                  <title>{`${d}: ${v.toLocaleString()} views`}</title>
                </g>
              );
            })}
          </svg>

          {/* Date Axis labels */}
          <div className="flex justify-between px-5 text-[10px] text-zinc-400 font-mono">
            {dayKeys.map((d, i) => {
              if (i % 2 === 0 || i === dayKeys.length - 1) {
                return <span key={d}>{d.slice(5)}</span>;
              }
              return <span key={d} className="invisible">-</span>;
            })}
          </div>
        </div>
      </div>

      {/* Heatmap Giờ Vàng (7 weekdays x 24 hours) */}
      <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="font-bold text-sm text-zinc-900 dark:text-white flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-500" />
              Bản Đồ Nhiệt Giờ Vàng (7 Ngày × 24 Giờ)
            </h3>
            <p className="text-xs text-zinc-400">
              Điểm tương tác & lượt xem trung vị 24h giúp tối ưu lịch đăng bài
            </p>
          </div>

          <div className="flex items-center gap-3">
            {appliedSuccess && (
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> Đã cập nhật khung giờ!
              </span>
            )}
            <button
              onClick={handleApplyGolden}
              disabled={applyingWindows}
              className="px-4 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-zinc-950 text-xs font-bold shadow-sm transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {applyingWindows ? "Đang áp dụng..." : "Áp dụng khung giờ vàng"}
            </button>
          </div>
        </div>

        {/* Top Recommended Slots Pills */}
        {heatmapData?.top_slots && heatmapData.top_slots.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="text-xs text-zinc-400 font-medium">Khung giờ đề xuất:</span>
            {heatmapData.top_slots.slice(0, 4).map((s, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-xs text-amber-800 dark:text-amber-300 font-medium"
              >
                <Flame className="w-3 h-3 text-amber-500" />
                <span>
                  {weekdays[s.weekday]}, {String(s.hour).padStart(2, "0")}:00
                </span>
                <span className="text-[10px] opacity-75">
                  ({s.median_views > 0 ? `${s.median_views.toLocaleString()}v` : `score ${s.score}`})
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Heatmap Grid */}
        <div className="overflow-x-auto">
          <div className="min-w-[650px]">
            {/* Hour header */}
            <div className="grid grid-cols-25 gap-1 text-[10px] text-zinc-400 text-center mb-1">
              <div className="text-left font-medium">Ngày</div>
              {Array.from({ length: 24 }).map((_, h) => (
                <div key={h} className="font-mono">
                  {h % 3 === 0 ? h : ""}
                </div>
              ))}
            </div>

            {/* Weekdays rows */}
            {weekdays.map((dayName, w) => {
              const row = heatmapData?.matrix?.[w] || [];
              return (
                <div key={w} className="grid grid-cols-25 gap-1 items-center mb-1">
                  <div className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 truncate">
                    {dayName}
                  </div>
                  {Array.from({ length: 24 }).map((_, h) => {
                    const slot = row[h] || { score: 10, median_views: 0, sample_count: 0 };
                    return (
                      <div
                        key={h}
                        onMouseEnter={() =>
                          setHoveredSlot({
                            weekday: w,
                            hour: h,
                            views: slot.median_views,
                            count: slot.sample_count,
                            score: slot.score,
                          })
                        }
                        onMouseLeave={() => setHoveredSlot(null)}
                        className={`h-6 rounded cursor-pointer transition-all hover:scale-110 hover:ring-2 hover:ring-amber-400 ${getSlotColor(
                          slot.score
                        )}`}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>

        {/* Hovered Slot Tooltip readout */}
        <div className="mt-3 text-xs text-zinc-500 h-5">
          {hoveredSlot ? (
            <span className="font-medium text-zinc-800 dark:text-zinc-200">
              {weekdays[hoveredSlot.weekday]}, lúc {String(hoveredSlot.hour).padStart(2, "0")}:00 —{" "}
              {hoveredSlot.views > 0
                ? `Median ${hoveredSlot.views.toLocaleString()} views (${hoveredSlot.count} bài)`
                : "Dữ liệu dự báo chuẩn theo thói quen xem mạng xã hội Việt Nam"}
            </span>
          ) : (
            <span>Di chuột vào từng ô để xem chi tiết lượt xem theo giờ</span>
          )}
        </div>
      </div>

      {/* Outliers & Creative Performance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outliers: Top vs Underperforming */}
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-zinc-900 dark:text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              Phân Tích Bài Đột Phá & Kém Hiệu Quả
            </h3>
            <span className="text-xs text-zinc-400">Ngưỡng 2.0x / 0.5x median</span>
          </div>

          <div className="space-y-3">
            {/* Top Outliers */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Bài bùng nổ (Top Outliers)
              </h4>
              {analyticsOverview?.outliers?.top_outliers?.length ? (
                analyticsOverview.outliers.top_outliers.map((o, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold text-zinc-900 dark:text-white">
                      <span className="truncate pr-2">{o.title}</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-bold flex-shrink-0">
                        {o.views.toLocaleString()} views ({o.ratio}x)
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-1">
                      {o.hypothesis}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-zinc-400 italic">Chưa có bài viết đột phá vượt 2x median.</p>
              )}
            </div>

            {/* Underperforming */}
            <div className="space-y-2 pt-2">
              <h4 className="text-xs font-bold uppercase text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" /> Bài cần cải thiện
              </h4>
              {analyticsOverview?.outliers?.underperforming?.length ? (
                analyticsOverview.outliers.underperforming.map((u, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold text-zinc-900 dark:text-white">
                      <span className="truncate pr-2">{u.title}</span>
                      <span className="text-rose-600 dark:text-rose-400 font-bold flex-shrink-0">
                        {u.views.toLocaleString()} views
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-1">
                      {u.hypothesis}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-zinc-400 italic">Không có bài viết dưới ngưỡng 0.5x.</p>
              )}
            </div>
          </div>
        </div>

        {/* Template & Blueprint Rankings */}
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-zinc-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" />
              Hiệu Quả Mẫu Video & Kịch Bản
            </h3>
            <button
              onClick={() => setAutomationModalOpen(true)}
              className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
            >
              Cấu hình quy tắc &rarr;
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] font-bold text-zinc-400 uppercase border-b border-zinc-100 dark:border-zinc-800">
                <tr>
                  <th className="pb-2">Mẫu Template</th>
                  <th className="pb-2 text-center">Số bài</th>
                  <th className="pb-2 text-right">Tổng Views</th>
                  <th className="pb-2 text-right">Views TB</th>
                  <th className="pb-2 text-right">ER %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/60 font-medium">
                {creativesData?.templates?.length ? (
                  creativesData.templates.slice(0, 5).map((t) => (
                    <tr key={t.template_id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30">
                      <td className="py-2.5 font-semibold text-zinc-900 dark:text-white font-mono">
                        {t.template_id}
                      </td>
                      <td className="py-2.5 text-center text-zinc-500">{t.post_count}</td>
                      <td className="py-2.5 text-right text-zinc-900 dark:text-white">
                        {t.total_views.toLocaleString()}
                      </td>
                      <td className="py-2.5 text-right text-indigo-600 dark:text-indigo-400 font-bold">
                        {t.avg_views.toLocaleString()}
                      </td>
                      <td className="py-2.5 text-right text-emerald-600 dark:text-emerald-400">
                        {t.avg_er}%
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-zinc-400">
                      Chưa có dữ liệu ghép mẫu template.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Learnings & Continuous Feedback Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-50/50 via-white to-purple-50/50 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-800/80 border border-indigo-100 dark:border-indigo-900/40 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-indigo-600 text-white shadow-sm">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-zinc-900 dark:text-white">
              Đúc Kết Tự Học & Khuyến Nghị Tuần Này
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Tổng hợp từ `analytics/learnings.md` và `recommendations.json` cho Session A & B
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white/80 dark:bg-zinc-950/50 border border-zinc-200/80 dark:border-zinc-800/80 text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed font-sans max-h-60 overflow-y-auto whitespace-pre-wrap">
          {learningsData?.learnings_md || "Đang tải báo cáo đúc kết..."}
        </div>
      </div>
    </div>
  );
}
