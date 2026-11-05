"use client";

import React from "react";
import { PolicyEditor } from "@/components/studio/PolicyEditor";

/** Chính sách nội dung của dự án (áp dụng xuyên suốt, node Kiểm tra chất lượng luôn đối chiếu). */
export function PolicyTab() {
  return (
    <div className="space-y-3 p-3.5 text-xs">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-foreground">Chính sách nội dung</h3>
        <p className="text-[13px] leading-relaxed text-muted-foreground">
          Áp dụng cho cả dự án: node Kiểm tra chất lượng luôn đối chiếu lời thoại, caption, kịch bản và prompt với chính sách này.
        </p>
      </div>
      <PolicyEditor />
    </div>
  );
}
