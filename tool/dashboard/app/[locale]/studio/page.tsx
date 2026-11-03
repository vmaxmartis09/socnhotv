"use client";

import React from "react";
import { StudioCanvas } from "@/components/canvas/StudioCanvas";
import { StudioBreadcrumb } from "@/components/studio/StudioBreadcrumb";

/** Studio: canvas toàn màn hình; breadcrumb, dock và hồ sơ nổi phía trên. */
export default function StudioPage() {
  return (
    <div className="relative flex h-full w-full min-w-0 overflow-clip bg-card">
      <StudioCanvas />
      <div className="pointer-events-none absolute inset-0 z-30">
        <StudioBreadcrumb />
      </div>
    </div>
  );
}
