"use client";

import React from "react";
import { ProjectsTab } from "@/components/project/ProjectsTab";
import { JobsList } from "@/components/jobs/JobsList";
import { Activity, FolderGit2 } from "@/components/ui/icons";
import { PageBar } from "@/components/studio/PageBar";

/** Sảnh: các dự án và những tiến trình đang chạy. Nhấn đúp vào dự án để vào Studio. */
export default function HomePage() {
  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="home" />
      <div className="scroll-quiet h-full overflow-y-auto">
      <div className="mx-auto max-w-[1000px] space-y-8 px-6 pb-8 pt-16 md:pr-20">
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <FolderGit2 className="h-4 w-4 text-muted-foreground" /> Dự án
          </h2>
          <ProjectsTab canCreate={false} />
        </section>
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Activity className="h-4 w-4 text-muted-foreground" /> Đang chạy
          </h2>
          <JobsList compact />
        </section>
      </div>
      </div>
    </div>
  );
}
