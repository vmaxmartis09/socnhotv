"use client";

import React from "react";
import { Plus } from "@/components/ui/icons";

export interface EmptyAction {
  key: string;
  icons: React.ComponentType<{ className?: string }>[];
  title: string;
  hint: string;
  onClick: () => void;
}

/** Trạng thái trống: ô viền nét đứt kèm icon, mỗi ô một việc thật có thể bấm để làm ngay. */
export function EmptyActions({ items }: { items: EmptyAction[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {items.map((it) => (
        <li key={it.key}>
          <button
            type="button"
            onClick={it.onClick}
            title={it.title}
            className="group flex h-full w-full items-center gap-3 rounded-2xl border border-dashed border-border p-4 text-left transition-colors hover:border-foreground/40 hover:bg-muted/30"
          >
            <span className="flex shrink-0 items-center gap-1 text-muted-foreground transition-colors group-hover:text-foreground">
              {it.icons.map((I, i) => (
                <I key={i} className="h-6 w-6" />
              ))}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[13px] font-medium text-foreground">{it.title}</span>
              <span className="block text-xs text-muted-foreground">{it.hint}</span>
            </span>
            <Plus className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:rotate-90 group-hover:text-foreground" />
          </button>
        </li>
      ))}
    </ul>
  );
}
