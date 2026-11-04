"use client";

import React, { useState, useEffect } from "react";
import type { ChannelStrategy } from "@/lib/api/intel";
import { intelApi } from "@/lib/api/intel";
import {
  Target,
  Trophy,
  Sparkles,
  TrendingUp,
  Layers,
  Clock,
  CheckCircle,
  AlertCircle,
} from "./icons";
import { Loader2, Calendar } from "@/components/ui/icons";

interface StrategyViewProps {
  projectId: string;
  onGoToIdeas?: () => void;
}

export function StrategyView({ projectId, onGoToIdeas }: StrategyViewProps) {
  const [strategy, setStrategy] = useState<ChannelStrategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  const loadStrategy = async () => {
    try {
      setLoading(true);
      const data = await intelApi.getStrategy(projectId);
      setStrategy(data);
    } catch (err) {
      console.error("Failed to load strategy:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStrategy();
  }, [projectId]);

  const handleGenerateFresh = async () => {
    setIsGenerating(true);
    try {
      const data = await intelApi.generateStrategy(projectId, strategy?.reference_channels || []);
      setStrategy(data);
    } catch (err: any) {
      alert(`Lỗi tạo chiến lược: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
        <span className="text-xs">Đang tải chiến lược kênh...</span>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-12 text-center">
        <Target className="mx-auto h-12 w-12 text-zinc-600" />
        <h3 className="mt-4 text-sm font-bold text-zinc-200">Chưa có Chiến lược Kênh</h3>
        <p className="mt-1 text-xs text-zinc-500 max-w-sm mx-auto">
          Tạo chiến lược kênh dựa trên các đối thủ đã học để xác lập định vị độc quyền và 4 pillars nội dung.
        </p>
        <button
          onClick={handleGenerateFresh}
          disabled={isGenerating}
          className="mt-6 inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg hover:bg-indigo-500"
        >
          {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Khởi tạo Chiến Lược Kênh
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Differentiation Banner */}
      <div className="rounded-2xl border border-indigo-500/40 bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-zinc-950 p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-indigo-400" />
            <h2 className="text-sm font-bold text-indigo-200 uppercase tracking-wider">
              Định Vị Khác Biệt Hoá Độc Quyền
            </h2>
          </div>
          <button
            onClick={handleGenerateFresh}
            disabled={isGenerating}
            className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1"
          >
            {isGenerating && <Loader2 className="h-3 w-3 animate-spin" />}
            Làm mới chiến lược
          </button>
        </div>
        <p className="mt-3 text-sm text-zinc-100 leading-relaxed font-medium">
          {strategy.differentiation}
        </p>
      </div>

      {/* 4 Core Pillars Grid */}
      <div>
        <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Layers className="h-4 w-4 text-indigo-400" />
          4 Trụ Cột Nội Dung Của Chúng Ta (Our Pillars)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {strategy.our_pillars.map((p, idx) => (
            <div
              key={p.id}
              className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-4 flex flex-col justify-between hover:border-zinc-700 transition"
            >
              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-400">Pillar {idx + 1}</span>
                  <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[11px] font-bold text-indigo-300 border border-indigo-500/20">
                    {p.target_ratio}%
                  </span>
                </div>
                <h4 className="mt-2 text-xs font-bold text-zinc-100">{p.name}</h4>
                <p className="mt-1 text-[11px] text-zinc-400 leading-relaxed">{p.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800/60">
                <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    style={{ width: `${p.target_ratio * 2.5}%` }}
                    className="h-full bg-indigo-500 rounded-full"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rules & Publishing Schedule */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Title & Thumbnail Rules */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-5 space-y-4">
          <div>
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle className="h-4 w-4 text-emerald-400" /> Quy Tắc Tiêu Đề
            </h4>
            <ul className="mt-2.5 space-y-1.5 text-xs text-zinc-300">
              {strategy.title_rules.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1 w-1 rounded-full bg-emerald-400 shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="pt-3 border-t border-zinc-800">
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-amber-400" /> Quy Tắc Thumbnail
            </h4>
            <ul className="mt-2.5 space-y-1.5 text-xs text-zinc-300">
              {strategy.thumbnail_rules.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1 w-1 rounded-full bg-amber-400 shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Schedule & Format Mix */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-5 space-y-4">
          <div>
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-indigo-400" /> Lịch Đăng Đề Xuất Theo Nền Tảng
            </h4>
            <div className="mt-2.5 space-y-2">
              {Object.entries(strategy.publishing_schedule).map(([platform, time]) => (
                <div
                  key={platform}
                  className="flex items-center justify-between rounded-lg bg-zinc-900/60 px-3 py-2 text-xs border border-zinc-800/60"
                >
                  <span className="font-semibold uppercase text-indigo-300">{platform}</span>
                  <span className="text-zinc-300">{time}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-zinc-800">
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-2">
              Tỉ Lệ Định Dạng (Format Mix)
            </h4>
            <div className="flex h-3 w-full rounded-full overflow-hidden bg-zinc-800">
              <div style={{ width: "20%" }} className="bg-purple-500" title="Hoạt hình 3D dài: 20%" />
              <div style={{ width: "40%" }} className="bg-indigo-500" title="Shorts/Reels: 40%" />
              <div style={{ width: "40%" }} className="bg-emerald-500" title="KOC Review & Sales: 40%" />
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-zinc-400">
              <span>Hoạt hình 3D (20%)</span>
              <span>Shorts/Reels (40%)</span>
              <span>KOC Review/Sales (40%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* 30-Day KPIs Cards */}
      <div>
        <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Trophy className="h-4 w-4 text-amber-400" />
          Mục Tiêu Tăng Trưởng 30 Ngày (30-Day KPIs)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-center">
            <span className="text-[11px] text-zinc-400 uppercase font-semibold">Lượt xem mục tiêu</span>
            <div className="mt-1 text-xl font-black text-indigo-400">
              {Number(strategy.kpi_30d.target_total_views || 500000).toLocaleString()}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-center">
            <span className="text-[11px] text-zinc-400 uppercase font-semibold">Followers mới</span>
            <div className="mt-1 text-xl font-black text-purple-400">
              +{Number(strategy.kpi_30d.target_subscribers || 15000).toLocaleString()}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-center">
            <span className="text-[11px] text-zinc-400 uppercase font-semibold">Click Link Tiếp Thị</span>
            <div className="mt-1 text-xl font-black text-emerald-400">
              {Number(strategy.kpi_30d.target_affiliate_clicks || 3500).toLocaleString()}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-center">
            <span className="text-[11px] text-zinc-400 uppercase font-semibold">Đơn hàng Affiliate</span>
            <div className="mt-1 text-xl font-black text-amber-400">
              {Number(strategy.kpi_30d.target_orders || 250).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Guardrails Banner & Action to Ideas */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-rose-950/50 bg-rose-950/15 p-4">
        <div className="space-y-1">
          <span className="text-xs font-bold text-rose-400 uppercase flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4" /> Hàng Rào Bản Quyền (Guardrails)
          </span>
          <p className="text-xs text-rose-200/90 leading-relaxed">
            Mọi tiêu đề bắt buộc vượt qua kiểm tra Rapidfuzz ratio &lt; 70% so với đối thủ; không copy nhận diện thương hiệu.
          </p>
        </div>

        {onGoToIdeas && (
          <button
            onClick={onGoToIdeas}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-500/25 shrink-0 hover:from-indigo-600 hover:to-purple-700"
          >
            <Sparkles className="h-4 w-4" />
            Xem Bảng Ý Tưởng Kanban
          </button>
        )}
      </div>
    </div>
  );
}
