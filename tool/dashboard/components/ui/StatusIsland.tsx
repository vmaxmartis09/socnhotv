"use client";

import { useShallow } from "zustand/react/shallow";
import React from "react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";
import { getRunPresetMode } from "@/lib/core-contracts";

/** Plain status line: a dot and a sentence. Run mode is stated clearly (Animatic, Mock, Full, Custom). */
export function StatusIsland({ className }: { className?: string }) {
  const s = useTranslations("shell");
  const { jobs, isMockMode, runPolicy } = useStudioStore(
    useShallow((st) => ({ jobs: st.jobs, isMockMode: st.isMockMode, runPolicy: st.runPolicy }))
  );
  const running = jobs.filter((j) => j.status === "running").length;
  const failed = jobs.filter((j) => j.status === "failed").length;

  const tone = failed > 0 ? "bg-semantic-danger" : running > 0 ? "bg-brand" : "bg-semantic-success";
  const text =
    failed > 0 ? s("failed", { count: failed }) : running > 0 ? s("running", { count: running }) : s("ready");

  const mode = runPolicy ? getRunPresetMode(runPolicy) : isMockMode ? "quick" : "animatic";
  const modeLabel =
    mode === "animatic"
      ? "Animatic ($0)"
      : mode === "quick"
        ? s("mock")
        : mode === "full"
          ? "Đầy đủ"
          : "Tuỳ chỉnh";

  return (
    <div className={cn("flex items-center gap-2 text-sm text-muted-foreground select-none", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", tone)} aria-hidden="true" />
      <span>{text}</span>
      <span aria-hidden="true">·</span>
      <span
        className={cn(
          mode === "animatic" && "text-brand font-medium",
          mode === "full" && "text-amber-600 dark:text-amber-400 font-medium"
        )}
      >
        {modeLabel}
      </span>
    </div>
  );
}
