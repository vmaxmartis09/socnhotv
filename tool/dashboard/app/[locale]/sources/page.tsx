"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { Database } from "@/components/ui/icons";

export default function SourcesPage() {
  const t = useTranslations("sources");

  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="sources" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-[1000px] space-y-6 px-6 pb-8 pt-16 md:pr-20">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-foreground">{t("title")}</h1>
                <p className="text-sm text-muted-foreground">{t("description")}</p>
              </div>
            </div>
            <div className="mt-6 rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              Module Session B (Nguồn & Trí tuệ nội dung) đang sẵn sàng để tích hợp.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
