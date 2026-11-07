"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Play,
  Square,
  RotateCcw,
  Check,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Search,
  Layers,
  ShieldCheck,
  DollarSign,
  Film,
  Sliders,
} from "@/components/ui/icons";
import { fetchProjectScriptEpisodes, type ScriptEpisode } from "@/lib/api/nodes";
import { CORE_URL } from "@/lib/repositories/core";
import { cn } from "@/lib/utils";

export interface BatchRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  graph?: any;
}

export interface EpisodeResultItem {
  episodeId: string;
  runId?: string;
  isSuccess: boolean;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  totalCostUsd: number;
  executedNodes: string[];
  skippedNodes: string[];
  failedNodes: string[];
  cachedNodes: string[];
  errors: Record<string, string>;
  outputVideoPath?: string;
  durationSec: number;
}

export interface BatchSummaryState {
  batchId: string;
  projectId: string;
  totalEpisodes: number;
  completedCount: number;
  failedCount: number;
  cancelledCount: number;
  totalCostUsd: number;
  isSuccess: boolean;
  episodeResults: EpisodeResultItem[];
  durationSec: number;
}

export function BatchRunModal({ isOpen, onClose, projectId, graph }: BatchRunModalProps) {
  const [episodes, setEpisodes] = useState<ScriptEpisode[]>([]);
  const [isLoadingEpisodes, setIsLoadingEpisodes] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Run config
  const [isMockMode, setIsMockMode] = useState(true);
  const [concurrency, setConcurrency] = useState<1 | 2>(1);
  const [confirmPaidRun, setConfirmPaidRun] = useState(false);

  // SpendGuard estimate
  const [isEstimating, setIsEstimating] = useState(false);
  const [estimateData, setEstimateData] = useState<any>(null);
  const [estimateError, setEstimateError] = useState<string | null>(null);

  // Execution state
  const [isRunning, setIsRunning] = useState(false);
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null);
  const [batchSummary, setBatchSummary] = useState<BatchSummaryState | null>(null);
  const [currentRunningEp, setCurrentRunningEp] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  // Load episodes when opened
  useEffect(() => {
    if (!isOpen || !projectId) return;
    setIsLoadingEpisodes(true);
    setEstimateData(null);
    setEstimateError(null);
    setBatchSummary(null);
    setRunError(null);

    fetchProjectScriptEpisodes(projectId)
      .then((items) => {
        setEpisodes(items);
        // Pre-select first 3 episodes by default if nothing selected
        if (items.length > 0) {
          setSelectedIds(new Set(items.slice(0, 3).map((e) => e.id)));
        }
      })
      .catch((err) => {
        console.error("Lỗi tải danh sách tập:", err);
      })
      .finally(() => {
        setIsLoadingEpisodes(false);
      });
  }, [isOpen, projectId]);

  // Filtered episodes
  const filteredEpisodes = useMemo(() => {
    if (!searchQuery.trim()) return episodes;
    const q = searchQuery.toLowerCase();
    return episodes.filter(
      (ep) => ep.id.toLowerCase().includes(q) || ep.title.toLowerCase().includes(q)
    );
  }, [episodes, searchQuery]);

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredEpisodes.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredEpisodes.map((e) => e.id)));
    }
  };

  const toggleSelectOne = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Estimate SpendGuard
  const handleEstimate = useCallback(async () => {
    if (selectedIds.size === 0) return;
    setIsEstimating(true);
    setEstimateError(null);
    try {
      const payload: any = {
        episodeIds: Array.from(selectedIds),
        mockMode: isMockMode,
        concurrency,
        confirmPaidRun,
      };
      if (graph) payload.graph = graph;

      const res = await fetch(`${CORE_URL}/projects/${encodeURIComponent(projectId)}/estimate-episodes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Lỗi ước tính chi phí (mã ${res.status})`);
      }
      const data = await res.json();
      setEstimateData(data);
    } catch (err: any) {
      setEstimateError(err.message || String(err));
    } finally {
      setIsEstimating(false);
    }
  }, [selectedIds, isMockMode, concurrency, confirmPaidRun, graph, projectId]);

  // Start batch run
  const handleStartBatch = async () => {
    if (selectedIds.size === 0) return;
    setIsRunning(true);
    setRunError(null);
    setBatchSummary(null);

    const epList = Array.from(selectedIds);
    // Initialize temporary summary for live feedback
    setBatchSummary({
      batchId: "batch_initiating",
      projectId,
      totalEpisodes: epList.length,
      completedCount: 0,
      failedCount: 0,
      cancelledCount: 0,
      totalCostUsd: 0,
      isSuccess: false,
      episodeResults: epList.map((id) => ({
        episodeId: id,
        isSuccess: false,
        status: "pending",
        totalCostUsd: 0,
        executedNodes: [],
        skippedNodes: [],
        failedNodes: [],
        cachedNodes: [],
        errors: {},
        durationSec: 0,
      })),
      durationSec: 0,
    });

    try {
      const payload: any = {
        episodeIds: epList,
        mockMode: isMockMode,
        concurrency,
        confirmPaidRun,
      };
      if (graph) payload.graph = graph;

      const res = await fetch(`${CORE_URL}/projects/${encodeURIComponent(projectId)}/run-episodes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 409) {
        const confJson = await res.json().catch(() => ({}));
        setEstimateData(confJson.estimate);
        setRunError(
          "Cần xác nhận chi phí trả phí trước khi tiếp tục. Vui lòng tick vào ô 'Xác nhận trả phí' và bấm lại."
        );
        setIsRunning(false);
        return;
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Lỗi chạy batch (mã ${res.status})`);
      }

      const summaryData: BatchSummaryState = await res.json();
      setBatchSummary(summaryData);
      setActiveBatchId(summaryData.batchId);
    } catch (err: any) {
      setRunError(err.message || String(err));
    } finally {
      setIsRunning(false);
      setCurrentRunningEp(null);
    }
  };

  // Cancel batch run
  const handleCancelBatch = async () => {
    try {
      await fetch(`${CORE_URL}/projects/${encodeURIComponent(projectId)}/run-episodes/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ batchId: activeBatchId || undefined }),
      });
    } catch (err) {
      console.error("Lỗi khi gửi yêu cầu hủy:", err);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => !isRunning && onClose()}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 10 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 10 }}
          className="relative flex flex-col w-full max-w-4xl max-h-[90vh] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/20">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-foreground">
                  Chạy Hàng Loạt Tập Phim (Batch Runner)
                </h2>
                <p className="text-xs text-muted-foreground">
                  Chọn N tập để chạy tuần tự theo cùng 1 flow mẫu. Cache theo tập, cách ly lỗi độc lập.
                </p>
              </div>
            </div>
            <button
              type="button"
              disabled={isRunning}
              onClick={onClose}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-50"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 scroll-quiet">
            {/* Run Error Banner */}
            {runError && (
              <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold">Thông báo lỗi:</p>
                  <p className="mt-0.5 leading-relaxed">{runError}</p>
                </div>
              </div>
            )}

            {/* Episode Selector Section */}
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-foreground">
                    Chọn các tập cần chạy ({selectedIds.size}/{episodes.length}):
                  </span>
                  <button
                    type="button"
                    onClick={toggleSelectAll}
                    disabled={isRunning || episodes.length === 0}
                    className="text-[11px] text-primary hover:underline font-medium disabled:opacity-50"
                  >
                    {selectedIds.size === filteredEpisodes.length ? "Bỏ chọn tất cả" : "Chọn tất cả lọc"}
                  </button>
                </div>

                {/* Search Box */}
                <div className="relative w-64">
                  <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="search"
                    placeholder="Tìm tên hoặc mã tập..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    disabled={isRunning}
                    className="h-8 w-full rounded-lg border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              {/* Episodes List */}
              <div className="max-h-52 overflow-y-auto rounded-xl border border-border bg-background/50 divide-y divide-border/60 scroll-quiet">
                {isLoadingEpisodes ? (
                  <div className="flex items-center justify-center p-8 text-xs text-muted-foreground gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <span>Đang nạp danh sách tập kịch bản...</span>
                  </div>
                ) : filteredEpisodes.length === 0 ? (
                  <div className="p-8 text-center text-xs text-muted-foreground">
                    Không tìm thấy tập nào phù hợp.
                  </div>
                ) : (
                  filteredEpisodes.map((ep) => {
                    const isSelected = selectedIds.has(ep.id);
                    return (
                      <label
                        key={ep.id}
                        className={cn(
                          "flex items-center gap-3 px-4 py-2.5 text-xs cursor-pointer select-none transition-colors",
                          isSelected ? "bg-primary/5 hover:bg-primary/10" : "hover:bg-accent/40",
                          isRunning && "pointer-events-none opacity-70"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectOne(ep.id)}
                          disabled={isRunning}
                          className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                        />
                        <div className="flex-1 min-w-0">
                          <span className="font-semibold text-foreground mr-2 font-mono">
                            {ep.id}
                          </span>
                          <span className="text-muted-foreground truncate">{ep.title}</span>
                        </div>
                      </label>
                    );
                  })
                )}
              </div>
            </div>

            {/* Execution Options & SpendGuard */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Left Column: Mode & Concurrency */}
              <div className="rounded-xl border border-border bg-muted/10 p-4 space-y-3.5">
                <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-primary" />
                  Cấu hình chế độ chạy
                </h3>

                {/* Mock Mode Switch */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-foreground">Chế độ Mock (Miễn phí)</p>
                    <p className="text-[11px] text-muted-foreground">
                      Dùng dữ liệu giả lập/ảnh tĩnh, không tốn API key và $0 chi phí.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={isRunning}
                    onClick={() => setIsMockMode(!isMockMode)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors",
                      isMockMode ? "bg-muted text-foreground" : "bg-primary text-primary-foreground"
                    )}
                  >
                    {isMockMode ? "Mock ($0)" : "Live (Model thật)"}
                  </button>
                </div>

                {/* Concurrency Selector */}
                <div className="flex items-center justify-between pt-1 border-t border-border/50">
                  <div>
                    <p className="text-xs font-medium text-foreground">Số tập chạy song song</p>
                    <p className="text-[11px] text-muted-foreground">
                      Tuần tự (1 tập) tránh nghẽn Core; 2 tập khi cần tốc độ.
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      disabled={isRunning}
                      onClick={() => setConcurrency(1)}
                      className={cn(
                        "h-7 px-2.5 rounded text-xs font-medium",
                        concurrency === 1
                          ? "bg-primary text-primary-foreground"
                          : "border border-border hover:bg-accent"
                      )}
                    >
                      1 (Tuần tự)
                    </button>
                    <button
                      type="button"
                      disabled={isRunning}
                      onClick={() => setConcurrency(2)}
                      className={cn(
                        "h-7 px-2.5 rounded text-xs font-medium",
                        concurrency === 2
                          ? "bg-primary text-primary-foreground"
                          : "border border-border hover:bg-accent"
                      )}
                    >
                      2 (Song song)
                    </button>
                  </div>
                </div>

                {/* Paid confirmation checkbox */}
                {!isMockMode && (
                  <label className="flex items-start gap-2 pt-1 border-t border-border/50 text-[11px] text-foreground cursor-pointer">
                    <input
                      type="checkbox"
                      checked={confirmPaidRun}
                      onChange={(e) => setConfirmPaidRun(e.target.checked)}
                      disabled={isRunning}
                      className="mt-0.5 rounded border-border"
                    />
                    <span>
                      Tôi xác nhận trừ chi phí hoá đơn API cho đợt chạy này (confirmPaidRun=true).
                    </span>
                  </label>
                )}
              </div>

              {/* Right Column: SpendGuard Preview */}
              <div className="rounded-xl border border-border bg-muted/10 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-500" />
                    Ước tính trần chi phí SpendGuard
                  </h3>
                  <button
                    type="button"
                    onClick={handleEstimate}
                    disabled={isEstimating || isRunning || selectedIds.size === 0}
                    className="text-[11px] font-medium text-primary hover:underline flex items-center gap-1 disabled:opacity-50"
                  >
                    {isEstimating ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <RotateCcw className="h-3 w-3" />
                    )}
                    <span>Tính lại</span>
                  </button>
                </div>

                {estimateData ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-border/40">
                      <span className="text-muted-foreground">Tổng chi phí ước tính ({estimateData.totalEpisodes} tập):</span>
                      <span className="font-semibold text-foreground">
                        ${estimateData.totalEstimatedCostUsd?.toFixed(4) || "0.0000"} USD
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-border/40">
                      <span className="text-muted-foreground">Ngân sách dự án còn lại:</span>
                      <span className="font-medium text-foreground">
                        ${estimateData.spendStatus?.remainingBudgetUsd?.toFixed(2) || "0.00"} USD
                      </span>
                    </div>
                    {estimateData.missingApiKeys?.length > 0 && (
                      <div className="rounded bg-destructive/10 p-2 text-[11px] text-destructive">
                        Thiếu khóa API: {estimateData.missingApiKeys.join(", ")}
                      </div>
                    )}
                    {estimateData.reason && (
                      <div className="rounded bg-destructive/10 p-2 text-[11px] text-destructive">
                        {estimateData.reason}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-4 text-center text-xs text-muted-foreground space-y-2">
                    <DollarSign className="h-6 w-6 text-muted-foreground/60" />
                    <p>Bấm &quot;Tính lại&quot; để kiểm tra số dư và chi phí theo SpendGuard trước khi chạy.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Batch Progress & Report Table (when running or completed) */}
            {batchSummary && (
              <div className="space-y-3 rounded-xl border border-border bg-card p-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
                      {isRunning ? (
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      ) : batchSummary.isSuccess ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                      )}
                      <span>
                        Tiến độ Batch: {batchSummary.completedCount}/{batchSummary.totalEpisodes} tập thành công
                      </span>
                    </h3>
                    <p className="text-[11px] text-muted-foreground">
                      Thời gian: {batchSummary.durationSec}s · Tổng chi phí thực tế: ${batchSummary.totalCostUsd.toFixed(4)} USD
                    </p>
                  </div>

                  {isRunning && (
                    <button
                      type="button"
                      onClick={handleCancelBatch}
                      className="px-3 py-1.5 rounded-lg border border-destructive/40 bg-destructive/10 text-xs font-medium text-destructive hover:bg-destructive/20 flex items-center gap-1.5"
                    >
                      <Square className="h-3 w-3" />
                      <span>Dừng chạy</span>
                    </button>
                  )}
                </div>

                {/* Per-Episode Result Table */}
                <div className="max-h-60 overflow-y-auto rounded-lg border border-border text-xs scroll-quiet">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-muted/40 sticky top-0 text-[11px] text-muted-foreground font-semibold border-b border-border">
                      <tr>
                        <th className="py-2 px-3">Tập</th>
                        <th className="py-2 px-3">Trạng thái</th>
                        <th className="py-2 px-3">Nodes</th>
                        <th className="py-2 px-3">Thời gian</th>
                        <th className="py-2 px-3">Chi phí</th>
                        <th className="py-2 px-3">Chi tiết / Tệp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                      {batchSummary.episodeResults.map((epRes) => (
                        <tr key={epRes.episodeId} className="hover:bg-muted/10">
                          <td className="py-2 px-3 font-mono font-medium text-foreground">
                            {epRes.episodeId}
                          </td>
                          <td className="py-2 px-3">
                            <span
                              className={cn(
                                "px-2 py-0.5 rounded-full text-[10px] font-semibold",
                                epRes.status === "completed" && "bg-emerald-500/10 text-emerald-500",
                                epRes.status === "failed" && "bg-destructive/10 text-destructive",
                                epRes.status === "cancelled" && "bg-amber-500/10 text-amber-500",
                                epRes.status === "running" && "bg-primary/10 text-primary",
                                epRes.status === "pending" && "bg-muted text-muted-foreground"
                              )}
                            >
                              {epRes.status === "completed" && "Hoàn thành"}
                              {epRes.status === "failed" && "Thất bại"}
                              {epRes.status === "cancelled" && "Đã hủy"}
                              {epRes.status === "running" && "Đang xử lý..."}
                              {epRes.status === "pending" && "Chờ"}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-[11px] text-muted-foreground">
                            {epRes.cachedNodes?.length > 0 ? (
                              <span className="text-emerald-500 font-medium">
                                {epRes.cachedNodes.length} cached / {epRes.executedNodes.length} chạy
                              </span>
                            ) : (
                              <span>{epRes.executedNodes.length} chạy</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-[11px] text-muted-foreground">
                            {epRes.durationSec}s
                          </td>
                          <td className="py-2 px-3 text-[11px] text-muted-foreground font-mono">
                            ${epRes.totalCostUsd.toFixed(4)}
                          </td>
                          <td className="py-2 px-3 text-[11px]">
                            {epRes.outputVideoPath ? (
                              <span className="text-primary font-mono truncate max-w-xs block">
                                {epRes.outputVideoPath}
                              </span>
                            ) : Object.keys(epRes.errors).length > 0 ? (
                              <span className="text-destructive truncate max-w-xs block" title={JSON.stringify(epRes.errors)}>
                                {Object.values(epRes.errors)[0]}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-muted/20">
            <div className="text-xs text-muted-foreground">
              {selectedIds.size === 0 ? (
                "Chưa chọn tập nào"
              ) : (
                <span>
                  Đã chọn <strong>{selectedIds.size}</strong> tập phim
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isRunning}
                className="h-9 px-4 rounded-lg border border-border bg-background text-xs font-medium text-foreground hover:bg-accent transition-colors disabled:opacity-50"
              >
                Đóng
              </button>

              <button
                type="button"
                onClick={handleStartBatch}
                disabled={isRunning || selectedIds.size === 0}
                className="h-9 px-4 rounded-lg bg-primary text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Đang chạy batch...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5" />
                    <span>Chạy {selectedIds.size} tập đã chọn</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
