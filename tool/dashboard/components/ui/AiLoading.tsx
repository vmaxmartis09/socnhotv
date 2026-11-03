"use client";

import React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

/** Trạng thái chờ chung cho mọi tác vụ AI: tia sáng xoay + chữ chạy ánh sáng; `lines` thêm khung xương. */
export function AiLoading({
  label = "AI đang làm việc…",
  lines = 0,
  className,
}: {
  label?: string;
  lines?: number;
  className?: string;
}) {
  return (
    <div role="status" aria-live="polite" className={cn("space-y-2", className)}>
      <div className="flex items-center gap-2 text-[13px] font-medium">
        <motion.span animate={{ rotate: 360, scale: [1, 1.15, 1] }} transition={{ repeat: Infinity, duration: 2.4, ease: "linear" }} className="text-brand">
          <Sparkles className="h-4 w-4" />
        </motion.span>
        <span className="ai-shimmer">{label}</span>
      </div>
      {lines > 0 && (
        <div className="space-y-1.5">
          {Array.from({ length: lines }, (_, i) => (
            <div key={i} className="ai-skeleton h-3 rounded-full" style={{ width: `${92 - i * 14}%` }} />
          ))}
        </div>
      )}
    </div>
  );
}
