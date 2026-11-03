"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { StudioCanvas } from "@/components/canvas/StudioCanvas";
import { RightPanel } from "@/components/studio/RightPanel";

export default function StudioHomePage() {
  const t = useTranslations("canvas");

  return (
    <div className="flex h-full w-full min-w-0 overflow-hidden bg-card">
      <h1 className="sr-only">{t("title")}</h1>
      <StudioCanvas />
      <RightPanel />
    </div>
  );
}
