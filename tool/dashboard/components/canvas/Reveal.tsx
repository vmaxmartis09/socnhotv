import React from "react";
import { cn } from "@/lib/utils";

/** Hiện/ẩn mượt bằng grid-rows 0fr↔1fr (không cần biết trước chiều cao). */
export function Reveal({ show, children }: { show: boolean; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "grid transition-[grid-template-rows,opacity] duration-200 ease-out",
        show ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
      )}
      aria-hidden={!show}
    >
      <div className="min-h-0 overflow-hidden">{children}</div>
    </div>
  );
}
