"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Sparkles, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useStudioStore } from "@/store";

export function StatusIsland({ className }: { className?: string }) {
  const { jobs, isMockMode } = useStudioStore();
  const runningJobs = jobs.filter((j) => j.status === "running");
  const failedJobs = jobs.filter((j) => j.status === "failed");

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/80 backdrop-blur-md shadow-subtle text-xs select-none transition-all",
        className
      )}
    >
      {runningJobs.length > 0 ? (
        <>
          <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />
          <span className="font-medium text-foreground">
            Đang chạy {runningJobs.length} tác vụ...
          </span>
        </>
      ) : failedJobs.length > 0 ? (
        <>
          <AlertCircle className="w-3.5 h-3.5 text-semantic-danger" />
          <span className="font-medium text-semantic-danger">
            {failedJobs.length} lỗi
          </span>
        </>
      ) : (
        <>
          <CheckCircle2 className="w-3.5 h-3.5 text-semantic-success" />
          <span className="text-muted-foreground">Sẵn sàng</span>
        </>
      )}

      {isMockMode && (
        <span className="ml-1 px-1.5 py-0.5 rounded-sm bg-primary/10 text-primary text-[10px] font-semibold tracking-wider uppercase">
          Mock Mode
        </span>
      )}
    </div>
  );
}
