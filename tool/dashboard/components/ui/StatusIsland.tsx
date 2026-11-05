"use client";

import { useShallow } from "zustand/react/shallow";
import React from "react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useStudioStore } from "@/store";

/** Plain status line: a dot and a sentence. Mock mode is stated once, in words. */
export function StatusIsland({ className }: { className?: string }) {
  const s = useTranslations("shell");
  const { jobs, isMockMode } = useStudioStore(
    useShallow((s) => ({ jobs: s.jobs, isMockMode: s.isMockMode }))
  );
  const running = jobs.filter((j) => j.status === "running").length;
  const failed = jobs.filter((j) => j.status === "failed").length;

  const tone = failed > 0 ? "bg-semantic-danger" : running > 0 ? "bg-brand" : "bg-semantic-success";
  const text =
    failed > 0 ? s("failed", { count: failed }) : running > 0 ? s("running", { count: running }) : s("ready");

  return (
    <div className={cn("flex items-center gap-2 text-sm text-muted-foreground select-none", className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", tone)} aria-hidden="true" />
      <span>{text}</span>
      {isMockMode && (
        <>
          <span aria-hidden="true">·</span>
          <span>{s("mock")}</span>
        </>
      )}
    </div>
  );
}
