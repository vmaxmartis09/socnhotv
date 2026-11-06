"use client";

import React, { memo } from "react";
import type { NodeProps, Node } from "@xyflow/react";
import { Layers } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export const GROUP_TYPE = "templateGroup";

export type TemplateGroupData = {
  nodeType: "group";
  label: string;
  templateId?: string;
  count?: number;
  status?: string;
  params?: Record<string, any>;
  generations?: any[];
} & Record<string, unknown>;

/** Khung Group: chứa toàn bộ node của một template. Kéo khung = kéo cả flow. */
function TemplateGroupNodeImpl({ data, selected }: NodeProps<Node<TemplateGroupData>>) {
  return (
    <div
      className={cn(
        "h-full w-full rounded-2xl border-2 border-dashed bg-card/30 transition-colors",
        selected ? "border-foreground/60" : "border-border"
      )}
    >
      <div className="flex items-center gap-2 px-4 py-3 text-left">
        <span className="flex h-7 w-7 items-center justify-center rounded-full border border-border bg-card">
          <Layers className="h-3.5 w-3.5 text-foreground" />
        </span>
        <span className="text-sm font-bold text-foreground">{data.label}</span>
        {typeof data.count === "number" && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-semibold text-muted-foreground tnum">
            {data.count} node
          </span>
        )}
      </div>
    </div>
  );
}

export const TemplateGroupNode = memo(TemplateGroupNodeImpl);
