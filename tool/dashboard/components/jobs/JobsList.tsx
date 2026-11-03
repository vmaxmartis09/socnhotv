"use client";

import { enterOnce } from "@/lib/motion";
import React, { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStudioStore } from "@/store";
import { useRouter } from "@/i18n/routing";
import type { Job } from "@/lib/repositories/types";
import { Loader2, CheckCircle2, AlertTriangle, Circle, ExternalLink, Image as ImageIcon, Video, Volume2, ScrollText, Film } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const TYPE_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  image_gen: ImageIcon,
  video_gen: Video,
  voice_tts: Volume2,
  script_analysis: ScrollText,
  render: Film,
};

function StatusIcon({ status }: { status: Job["status"] }) {
  if (status === "running") return <Loader2 className="h-4 w-4 animate-spin text-brand" />;
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-semantic-success" />;
  if (status === "failed") return <AlertTriangle className="h-4 w-4 text-semantic-danger" />;
  return <Circle className="h-4 w-4 text-muted-foreground" />;
}

const statusLabel: Record<Job["status"], string> = {
  pending: "Chờ",
  queued: "Trong hàng đợi",
  running: "Đang chạy",
  completed: "Xong",
  failed: "Lỗi",
};

/** Danh sách tiến trình; `compact` dùng ở Sảnh, bản đầy đủ có chi tiết bên phải và nút focus. */
export function JobsList({ compact = false }: { compact?: boolean }) {
  const { jobs, projects, switchProject, setSelectedNodeId, flashNode } = useStudioStore();
  const router = useRouter();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const sorted = useMemo(
    () =>
      [...jobs].sort((a, b) => {
        const live = (j: Job) => (j.status === "running" || j.status === "queued" ? 0 : 1);
        return live(a) - live(b) || b.createdAt.localeCompare(a.createdAt);
      }),
    [jobs]
  );
  const selected = sorted.find((j) => j.id === selectedId) ?? (compact ? undefined : sorted[0]);
  const projectName = (id: string) => projects.find((p) => p.id === id)?.name ?? id;

  const focus = (j: Job) => {
    switchProject(j.projectId);
    router.push("/studio");
    if (j.nodeId) {
      window.setTimeout(() => {
        setSelectedNodeId(j.nodeId!);
        flashNode(j.nodeId!);
      }, 400);
    }
  };

  if (sorted.length === 0) {
    return <p className={cn("text-sm text-muted-foreground", !compact && "p-6")}>Chưa có tiến trình nào. Chạy một node hoặc cả chuỗi trong Studio để xem ở đây.</p>;
  }

  const row = (j: Job) => {
    const Icon = TYPE_ICON[j.type] ?? Circle;
    const active = selected?.id === j.id;
    return (
      <motion.li key={j.id} layout initial={enterOnce(`job:${j.id}`, { opacity: 0, y: 6 })} animate={{ opacity: 1, y: 0 }}>
        <button
          type="button"
          onClick={() => setSelectedId(j.id)}
          onDoubleClick={() => focus(j)}
          title="Nhấn đúp để focus trong Studio"
          className={cn(
            "flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-colors",
            active ? "border-foreground bg-card" : "border-border bg-card hover:bg-muted/30"
          )}
        >
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent"><Icon className="h-4 w-4" /></span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[13px] font-medium text-foreground">{j.type}{j.nodeId ? ` · ${j.nodeId}` : ""}</span>
            <span className="block truncate text-xs text-muted-foreground">{projectName(j.projectId)}{j.model ? ` · ${j.model}` : ""}</span>
            {j.status === "running" && (
              <span className="mt-1.5 block h-1 overflow-hidden rounded-full bg-muted">
                <motion.span className="block h-full bg-brand" animate={{ width: `${Math.max(4, j.progress)}%` }} />
              </span>
            )}
          </span>
          <span title={statusLabel[j.status]}><StatusIcon status={j.status} /></span>
        </button>
      </motion.li>
    );
  };

  if (compact) return <ul className="space-y-2">{sorted.slice(0, 6).map(row)}</ul>;

  return (
    <div className="grid h-full grid-cols-1 md:grid-cols-[minmax(280px,380px)_1fr]">
      <ul className="scroll-quiet space-y-2 overflow-y-auto border-r border-border p-4">{sorted.map(row)}</ul>
      <div className="scroll-quiet overflow-y-auto p-6 md:pr-20">
        <AnimatePresence mode="wait">
          {selected && (
            <motion.div key={selected.id} initial={enterOnce(`jd:${selected.id}`, { opacity: 0, x: 12 })} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="space-y-4">
              <div className="flex items-center gap-2">
                <StatusIcon status={selected.status} />
                <h2 className="text-base font-semibold">{selected.type}{selected.nodeId ? ` · ${selected.nodeId}` : ""}</h2>
                <button type="button" title="Focus trong Studio" aria-label="Focus trong Studio" onClick={() => focus(selected)} className="ml-auto flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground active:scale-90">
                  <ExternalLink className="h-4 w-4" />
                </button>
              </div>
              <dl className="grid grid-cols-2 gap-2 text-[13px] sm:grid-cols-4">
                {[
                  ["Dự án", projectName(selected.projectId)],
                  ["Trạng thái", statusLabel[selected.status]],
                  ["Tiến độ", `${Math.round(selected.progress)}%`],
                  ["Chi phí", `$${(selected.actualCostUsd || selected.estimatedCostUsd || 0).toFixed(2)}`],
                ].map(([k, v]) => (
                  <div key={k} className="rounded-xl border border-border p-3">
                    <dt className="text-xs text-muted-foreground">{k}</dt>
                    <dd className="mt-0.5 truncate font-medium tnum">{v}</dd>
                  </div>
                ))}
              </dl>
              {selected.outputUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={selected.outputUrl} alt="" className="max-h-72 rounded-xl border border-border object-contain" />
              )}
              <section className="space-y-1.5">
                <h3 className="text-[13px] font-semibold">Nhật ký</h3>
                <pre className="scroll-quiet max-h-72 overflow-auto whitespace-pre-wrap rounded-xl border border-border bg-muted/20 p-3 font-mono text-xs leading-relaxed">
                  {(selected.logs ?? []).join("\n") || "—"}
                </pre>
              </section>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
