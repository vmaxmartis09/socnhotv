"use client";

import React from "react";
import { TemplatesView } from "@/components/templates/TemplatesView";

export default function TemplatesPage() {
  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-background">
      <TemplatesView className="flex-1" />
    </div>
  );
}
