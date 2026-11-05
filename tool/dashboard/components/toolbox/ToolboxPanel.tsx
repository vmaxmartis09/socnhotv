"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { enterOnce } from "@/lib/motion";
import {
  Wrench,
  Play,
  CheckCircle2,
  Sparkles,
  Layers,
  Mic,
  Image as ImageIcon,
  Activity,
  FileText,
  Clock,
  RotateCcw,
  Check
} from "@/components/ui/icons";
import { AiLoading } from "@/components/ui/AiLoading";
import { cn } from "@/lib/utils";

interface ToolItem {
  id: string;
  name: string;
  version: string;
  category: string;
  status: "verified" | "installed" | "planned" | "broken";
  license?: { code: string; commercial_ok: boolean };
  requires_gpu: boolean;
  requires_ffmpeg: boolean;
}

export function ToolboxPanel() {
  const [activeSubTab, setActiveSubTab] = useState<"tools" | "cutouts" | "audio" | "voices">("tools");
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [vaultData, setVaultData] = useState<{ cutouts: any[]; audios: any[]; voices: any[] }>({
    cutouts: [],
    audios: [],
    voices: []
  });
  const [loading, setLoading] = useState(true);
  const [runningTool, setRunningTool] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<any>(null);

  // Fetch tools and vault data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [toolsRes, vaultsRes] = await Promise.all([
        fetch("/api/toolbox?action=list").then((r) => r.json()),
        fetch("/api/toolbox?action=vaults").then((r) => r.json())
      ]);

      if (toolsRes.ok) setTools(toolsRes.tools);
      if (vaultsRes.ok) setVaultData(vaultsRes.vaults);
    } catch (err) {
      console.error("Failed to load toolbox data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunSample = async (toolId: string) => {
    try {
      setRunningTool(toolId);
      setRunResult(null);

      let inData: any = { params: {}, inputs: [] };
      if (toolId === "bg-remove") {
        inData = {
          params: { model: "u2net" },
          inputs: ["data/projects/soc-nho-tv/characters/soc_nho/soc_nho_01.png"]
        };
      } else if (toolId === "stt-align") {
        inData = {
          params: { model_size: "small", language: "vi" },
          inputs: ["data/shared/voice_vault/soc-nho/cloned_default_sample.mp3"]
        };
      }

      const res = await fetch("/api/toolbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ toolId, inData })
      });
      const data = await res.json();
      setRunResult(data);
      // Refresh vaults after run
      fetchData();
    } catch (err: any) {
      setRunResult({ ok: false, error: { message: err.message } });
    } finally {
      setRunningTool(null);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden text-left bg-background text-foreground select-none">
      {/* Top Header */}
      <div className="p-3 border-b border-border space-y-1 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-brand/10 text-brand">
              <Wrench className="w-4 h-4" />
            </span>
            <h2 className="text-[14px] font-semibold tracking-tight">Toolbox Cục Bộ</h2>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-success/10 text-success font-medium">
            CPU Offline
          </span>
        </div>
        <p className="text-[12px] text-muted-foreground">
          Công cụ video độc lập, chạy CPU, chia sẻ tài nguyên qua Kho dùng chung.
        </p>

        {/* Sub-tab pills */}
        <div className="flex items-center gap-1 pt-2">
          {(
            [
              { id: "tools", label: "Công cụ", count: tools.length },
              { id: "cutouts", label: "Tách nền", count: vaultData.cutouts.length },
              { id: "audio", label: "Canh từ", count: vaultData.audios.length },
              { id: "voices", label: "Giọng", count: vaultData.voices.length }
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={cn(
                "px-2.5 py-1 text-[11px] rounded-md font-medium transition-colors flex items-center gap-1.5",
                activeSubTab === tab.id
                  ? "bg-foreground/10 text-foreground font-semibold"
                  : "text-muted-foreground hover:bg-foreground/5"
              )}
            >
              <span>{tab.label}</span>
              <span className="text-[10px] opacity-70">({tab.count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 scroll-quiet">
        {loading ? (
          <div className="p-6">
            <AiLoading label="Đang quét danh mục công cụ..." lines={3} />
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {/* SUB-TAB 1: TOOLS LIST */}
            {activeSubTab === "tools" && (
              <motion.div
                key="subtab-tools"
                initial={enterOnce("toolbox-list", { opacity: 0, y: 4 })}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-3"
              >
                {/* Running status banner */}
                {runningTool && (
                  <div className="p-3 rounded-lg border border-brand/20 bg-brand/5 space-y-2">
                    <AiLoading label={`Đang chạy thực thi [${runningTool}]...`} lines={2} />
                  </div>
                )}

                {/* Last run result preview */}
                {runResult && !runningTool && (
                  <div
                    className={cn(
                      "p-3 rounded-lg border text-[12px] space-y-1.5",
                      runResult.ok
                        ? "border-success/30 bg-success/5 text-foreground"
                        : "border-destructive/30 bg-destructive/5 text-destructive"
                    )}
                  >
                    <div className="flex items-center justify-between font-medium">
                      <span>{runResult.ok ? "Chạy thành công!" : "Lỗi thực thi"}</span>
                      {runResult.result?.elapsed_s && (
                        <span className="text-[10px] text-muted-foreground">
                          {runResult.result.elapsed_s}s
                        </span>
                      )}
                    </div>
                    {runResult.ok && runResult.result?.outputs?.length > 0 && (
                      <div className="text-[11px] text-muted-foreground space-y-0.5">
                        {runResult.result.outputs.map((out: any, i: number) => (
                          <div key={i} className="truncate">
                            • <span className="font-semibold text-foreground">{out.kind}:</span> {out.path}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Tool Cards */}
                {tools.map((tool) => {
                  const isVerified = tool.status === "verified";
                  return (
                    <div
                      key={tool.id}
                      className="p-3 rounded-xl border border-border bg-card/60 hover:bg-card hover:border-foreground/20 transition-all space-y-2.5 text-left shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-1.5">
                            <span className="font-medium text-[13px]">{tool.name}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-foreground/5 text-muted-foreground">
                              v{tool.version}
                            </span>
                          </div>
                          <p className="text-[11px] text-muted-foreground font-mono">{tool.id}</p>
                        </div>

                        {/* Status Tag */}
                        <span
                          className={cn(
                            "text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0",
                            isVerified
                              ? "bg-success/10 text-success"
                              : tool.status === "installed"
                              ? "bg-brand/10 text-brand"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {tool.status.toUpperCase()}
                        </span>
                      </div>

                      {/* Capabilities & License Chips */}
                      <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                        <span className="px-1.5 py-0.5 rounded bg-foreground/5 text-muted-foreground">
                          {tool.requires_gpu ? "GPU Required" : "CPU Capable"}
                        </span>
                        {tool.requires_ffmpeg && (
                          <span className="px-1.5 py-0.5 rounded bg-foreground/5 text-muted-foreground">
                            FFmpeg
                          </span>
                        )}
                        {tool.license?.code && (
                          <span className="px-1.5 py-0.5 rounded bg-foreground/5 text-muted-foreground">
                            {tool.license.code}
                          </span>
                        )}
                      </div>

                      {/* Action Bar */}
                      <div className="pt-1 flex items-center justify-between border-t border-border/50 text-[11px]">
                        <span className="text-[10px] text-muted-foreground">
                          {tool.id === "bg-remove" && "Mẫu: soc_nho_01.png"}
                          {tool.id === "stt-align" && "Mẫu: cloned_default_sample.mp3"}
                          {tool.id === "ffmpeg-bin" && "Static 9.0.2 Bundle"}
                        </span>
                        {isVerified && (
                          <button
                            onClick={() => handleRunSample(tool.id)}
                            disabled={runningTool === tool.id}
                            className="px-2.5 py-1 rounded-md bg-brand text-brand-foreground hover:opacity-90 active:scale-95 transition-all flex items-center gap-1 text-[11px] font-medium"
                            data-tip="Chạy thử nghiệm trên mẫu có sẵn"
                          >
                            <Play className="w-3 h-3 fill-current" />
                            <span>Chạy thử</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </motion.div>
            )}

            {/* SUB-TAB 2: CUTOUTS VAULT */}
            {activeSubTab === "cutouts" && (
              <motion.div
                key="subtab-cutouts"
                initial={enterOnce("toolbox-cutouts", { opacity: 0, y: 4 })}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-3"
              >
                {vaultData.cutouts.length === 0 ? (
                  <div className="p-6 rounded-xl border border-dashed border-border text-center space-y-2">
                    <ImageIcon className="w-6 h-6 mx-auto text-muted-foreground" />
                    <p className="text-[12px] text-muted-foreground font-medium">Chưa có ảnh tách nền</p>
                    <button
                      onClick={() => handleRunSample("bg-remove")}
                      className="text-[11px] text-brand hover:underline"
                    >
                      + Chạy tách nền mẫu Bi ngay
                    </button>
                  </div>
                ) : (
                  vaultData.cutouts.map((item: any) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl border border-border bg-card/60 space-y-2 text-left"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-medium">#{item.id}</span>
                        <span className="text-muted-foreground">
                          {item.metadata?.width}x{item.metadata?.height}
                        </span>
                      </div>
                      <div className="rounded-lg border border-border bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#27272a_1px,transparent_1px)] [background-size:12px_12px] p-2 flex items-center justify-center">
                        <img
                          src={`/api/toolbox/preview?path=${encodeURIComponent(item.files?.cutout || "")}`}
                          alt="Cutout Preview"
                          className="max-h-36 object-contain"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      </div>
                      <div className="text-[10px] text-muted-foreground truncate">
                        Nguồn: {item.source}
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {/* SUB-TAB 3: AUDIO VAULT */}
            {activeSubTab === "audio" && (
              <motion.div
                key="subtab-audio"
                initial={enterOnce("toolbox-audio", { opacity: 0, y: 4 })}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-3"
              >
                {vaultData.audios.length === 0 ? (
                  <div className="p-6 rounded-xl border border-dashed border-border text-center space-y-2">
                    <Mic className="w-6 h-6 mx-auto text-muted-foreground" />
                    <p className="text-[12px] text-muted-foreground font-medium">Chưa có audio phiên âm</p>
                    <button
                      onClick={() => handleRunSample("stt-align")}
                      className="text-[11px] text-brand hover:underline"
                    >
                      + Phiên âm mẫu giọng Bi ngay
                    </button>
                  </div>
                ) : (
                  vaultData.audios.map((item: any) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl border border-border bg-card/60 space-y-2 text-left"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-medium">#{item.id}</span>
                        <span className="text-muted-foreground">{item.metadata?.duration}s</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-foreground/5 text-[12px] font-medium leading-relaxed">
                        "{item.metadata?.text_preview}"
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <span>Đã canh {item.metadata?.word_count || 16} từ karaoke</span>
                        <span>{item.metadata?.language?.toUpperCase()}</span>
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {/* SUB-TAB 4: VOICE VAULT */}
            {activeSubTab === "voices" && (
              <motion.div
                key="subtab-voices"
                initial={enterOnce("toolbox-voices", { opacity: 0, y: 4 })}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-2.5"
              >
                {vaultData.voices.map((v: any) => {
                  const m = v.metadata || {};
                  const isReady = m.status === "ready";
                  return (
                    <div
                      key={v.id}
                      className="p-2.5 rounded-xl border border-border bg-card/60 flex items-center justify-between gap-2"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[12px] font-medium">{m.display_name || v.id}</span>
                          <span className="text-[10px] font-mono text-muted-foreground">({v.id})</span>
                        </div>
                        <div className="text-[10px] text-muted-foreground">
                          Aliases: {m.aliases?.join(", ") || "none"}
                        </div>
                      </div>
                      <span
                        className={cn(
                          "text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0",
                          isReady ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                        )}
                      >
                        {m.status}
                      </span>
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
