"use client";

import React, { useState } from "react";
import type { ChannelAnalysisResponse } from "@/lib/api/intel";
import {
  BarChart3,
  Flame,
  Gauge,
  Clock,
  TrendingUp,
  Tv,
  ExternalLink,
  Brain,
  Sparkles,
} from "./icons";


interface ChannelDetailViewProps {
  analysis: ChannelAnalysisResponse;
  projectId: string;
  onAnalyzeSource?: (sourceId: string) => void;
}

const DAYS_OF_WEEK = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"];

export function ChannelDetailView({
  analysis,
  projectId,
  onAnalyzeSource,
}: ChannelDetailViewProps) {
  const { channel_meta, stats, pillars, schedule_heatmap, top_outliers, title_patterns } =
    analysis;

  const [activeTab, setActiveTab] = useState<"overview" | "pillars" | "outliers" | "schedule">("overview");

  // SVG Chart data: top 15 outlier views normalized
  const chartVideos = top_outliers.slice(0, 12);
  const maxViews = Math.max(...chartVideos.map((v) => v.view_count), 1000);
  const chartHeight = 120;
  const chartWidth = 500;

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-xl space-y-6">
      {/* Channel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden flex items-center justify-center shrink-0">
            {channel_meta.avatar ? (
              <img src={channel_meta.avatar} alt={channel_meta.name} className="h-full w-full object-cover" />
            ) : (
              <Tv className="h-6 w-6 text-indigo-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-zinc-100">{channel_meta.name}</h2>
              <a
                href={channel_meta.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 hover:text-zinc-300"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
            <p className="text-xs text-zinc-400">
              Đã phân tích <span className="font-semibold text-zinc-200">{stats.total_videos}</span> video • Lịch đăng:{" "}
              <span className="font-semibold text-indigo-400">{stats.upload_cadence}</span>
            </p>
          </div>
        </div>

        {/* Quick stat pills */}
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-zinc-900 px-3 py-1.5 border border-zinc-800 text-center">
            <span className="text-[10px] text-zinc-400 uppercase font-semibold">View Trung Vị</span>
            <div className="text-sm font-bold text-zinc-100">
              {stats.median_views.toLocaleString()}
            </div>
          </div>
          <div className="rounded-xl bg-zinc-900 px-3 py-1.5 border border-zinc-800 text-center">
            <span className="text-[10px] text-zinc-400 uppercase font-semibold">Tỉ Lệ Shorts</span>
            <div className="text-sm font-bold text-indigo-400">
              {Math.round(stats.shorts_ratio * 100)}%
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex rounded-lg bg-zinc-900 p-1 border border-zinc-800 max-w-md">
        {[
          { id: "overview", label: "Tổng quan & Outliers" },
          { id: "pillars", label: `Chủ đề (${pillars.length})` },
          { id: "schedule", label: "Lịch đăng Heatmap" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition ${
              activeTab === t.id
                ? "bg-zinc-800 text-white shadow"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Overview & SVG Chart */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Top Outlier Chart (Pure SVG) */}
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
                <BarChart3 className="h-4 w-4 text-indigo-400" />
                Biểu đồ phân phối Lượt xem các Video Outlier
              </span>
              <span className="text-[11px] text-zinc-500">Đỉnh: {maxViews.toLocaleString()} views</span>
            </div>

            <div className="w-full overflow-x-auto">
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-32 overflow-visible">
                {/* Horizontal gridlines */}
                {[0.25, 0.5, 0.75, 1.0].map((ratio) => {
                  const y = chartHeight - ratio * (chartHeight - 20);
                  return (
                    <line
                      key={ratio}
                      x1="0"
                      y1={y}
                      x2={chartWidth}
                      y2={y}
                      stroke="#27272a"
                      strokeDasharray="3 3"
                    />
                  );
                })}

                {/* Bars */}
                {chartVideos.map((v, i) => {
                  const barWidth = 24;
                  const gap = (chartWidth - chartVideos.length * barWidth) / (chartVideos.length + 1);
                  const x = gap + i * (barWidth + gap);
                  const h = Math.max((v.view_count / maxViews) * (chartHeight - 25), 4);
                  const y = chartHeight - h;
                  const isTop = i === 0;

                  return (
                    <g key={v.id} className="group cursor-pointer">
                      <title>{`${v.title}: ${v.view_count.toLocaleString()} views (x${v.outlier_score} median)`}</title>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={h}
                        rx="4"
                        className={isTop ? "fill-rose-500" : "fill-indigo-500 hover:fill-indigo-400"}
                      />
                      <text
                        x={x + barWidth / 2}
                        y={chartHeight + 12}
                        textAnchor="middle"
                        className="text-[9px] fill-zinc-500"
                      >
                        #{i + 1}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Top Outlier Table */}
          <div>
            <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Flame className="h-4 w-4 text-rose-400" />
              Top Video Đột biến Lượt xem (Outlier Score)
            </h3>
            <div className="space-y-2">
              {top_outliers.slice(0, 8).map((vid, idx) => (
                <div
                  key={vid.id}
                  className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 hover:border-zinc-700 transition"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-800 text-xs font-bold text-zinc-300 shrink-0">
                      {idx + 1}
                    </span>
                    <div className="h-10 w-16 rounded bg-zinc-800 shrink-0 overflow-hidden">
                      {vid.thumbnail ? (
                        <img src={vid.thumbnail} alt={vid.title} className="h-full w-full object-cover" />
                      ) : null}
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-xs font-semibold text-zinc-200 truncate">{vid.title}</h4>
                      <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                        <span>{vid.view_count.toLocaleString()} views</span>
                        <span>•</span>
                        <span className="font-semibold text-rose-400">x{vid.outlier_score} trung vị</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <a
                      href={vid.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded-lg border border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Title Patterns */}
          {title_patterns.length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
              <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider block mb-2">
                Khuôn mẫu tiêu đề thành công
              </span>
              <div className="flex flex-wrap gap-2">
                {title_patterns.map((pat, idx) => (
                  <span
                    key={idx}
                    className="rounded-lg bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-200 border border-zinc-800 font-mono"
                  >
                    "{pat}"
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Pillars */}
      {activeTab === "pillars" && (
        <div className="space-y-4">
          <span className="text-xs text-zinc-400 block">
            Phân tích cụm chủ đề nội dung (Pillars) chiếm tỉ trọng lượt xem cao nhất của kênh:
          </span>

          <div className="space-y-3">
            {pillars.map((p, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-2"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/20 text-indigo-400 font-bold text-[11px]">
                      {idx + 1}
                    </span>
                    <h4 className="font-bold text-zinc-100">{p.name}</h4>
                  </div>
                  <div className="text-zinc-400 text-[11px]">
                    <span className="font-semibold text-zinc-200">{p.video_count} videos</span> ({p.video_pct}%) •{" "}
                    <span className="font-semibold text-indigo-300">{p.total_views.toLocaleString()} views</span> ({p.view_pct}%)
                  </div>
                </div>

                {/* Percentage progress bar */}
                <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden flex">
                  <div
                    style={{ width: `${p.view_pct}%` }}
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Heatmap */}
      {activeTab === "schedule" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">
              Heatmap Thời Điểm Đăng Video (Thứ trong tuần x Giờ trong ngày)
            </span>
            <span className="text-xs text-indigo-400 font-semibold">{stats.upload_cadence}</span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="min-w-[600px] space-y-1.5">
              {/* Hour headers: 0h, 6h, 12h, 18h, 23h */}
              <div className="flex items-center text-[10px] text-zinc-500 pl-20">
                <span className="flex-1">0h</span>
                <span className="flex-1">4h</span>
                <span className="flex-1">8h</span>
                <span className="flex-1">12h</span>
                <span className="flex-1">16h</span>
                <span className="flex-1">20h</span>
                <span className="flex-1">23h</span>
              </div>

              {/* Day rows */}
              {schedule_heatmap.map((hours, dayIdx) => (
                <div key={dayIdx} className="flex items-center gap-2">
                  <span className="w-16 text-[11px] font-semibold text-zinc-400 shrink-0">
                    {DAYS_OF_WEEK[dayIdx]}
                  </span>
                  <div className="flex-1 grid grid-cols-24 gap-1">
                    {hours.map((val, hr) => {
                      let bgClass = "bg-zinc-800/40";
                      if (val > 4) bgClass = "bg-indigo-500";
                      else if (val > 2) bgClass = "bg-indigo-600";
                      else if (val > 0) bgClass = "bg-indigo-900";

                      return (
                        <div
                          key={hr}
                          title={`${DAYS_OF_WEEK[dayIdx]} lúc ${hr}h: ${val} video`}
                          className={`h-5 rounded-sm ${bgClass} transition hover:scale-110 cursor-pointer`}
                        />
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
