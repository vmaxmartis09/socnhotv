"use client";

import React from "react";
import { useParams } from "next/navigation";
import { PageBar } from "@/components/studio/PageBar";
import { EpisodeBuildPanel } from "@/components/renders/EpisodeBuildPanel";
import { useStudioStore } from "@/store";

export default function EpisodeRenderPage() {
  const params = useParams();
  const eid = String(params?.eid || "ep_01");
  const activeProjectId = useStudioStore((state) => state.activeProjectId || "soc-nho-tv");

  return (
    <div className="relative h-full w-full overflow-y-auto bg-slate-950 text-slate-100">
      <PageBar page="renders" />
      <div className="p-4 sm:p-6 lg:p-8">
        <EpisodeBuildPanel projectId={activeProjectId} episodeId={eid} />
      </div>
    </div>
  );
}
