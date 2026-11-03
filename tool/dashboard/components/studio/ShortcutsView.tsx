"use client";

import React from "react";
import { SHORTCUT_GROUPS } from "@/lib/shortcuts";

/** Tất cả phím tắt của ứng dụng ở một chỗ. */
export function ShortcutsView() {
  return (
    <div className="space-y-5 p-4">
      {SHORTCUT_GROUPS.map((g) => (
        <section key={g.title} className="space-y-2">
          <h3 className="text-[13px] font-semibold text-foreground">{g.title}</h3>
          <dl className="divide-y divide-border rounded-xl border border-border">
            {g.items.map((it) => (
              <div key={it.label} className="flex items-center justify-between gap-3 px-3 py-2">
                <dt className="text-[13px] text-muted-foreground">{it.label}</dt>
                <dd className="flex shrink-0 items-center gap-1">
                  {it.keys.map((k) => (
                    <kbd key={k} className="rounded-md border border-border bg-muted/40 px-1.5 py-0.5 font-mono text-[11px] text-foreground">
                      {k}
                    </kbd>
                  ))}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  );
}
