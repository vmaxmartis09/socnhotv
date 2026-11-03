"use client";

import React from "react";
import { JobsList } from "@/components/jobs/JobsList";
import { PageBar } from "@/components/studio/PageBar";

/** Trang công việc: danh sách tiến trình + chi tiết, bấm "focus" để nhảy tới node trong Studio. */
export default function JobsPage() {
  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="jobs" />
      <div className="h-full pt-14">
        <JobsList />
      </div>
    </div>
  );
}
