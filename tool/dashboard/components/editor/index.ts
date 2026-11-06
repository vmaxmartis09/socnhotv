import React from "react";
import { usePreview } from "@/lib/preview";
import { TimelineEditor } from "./TimelineEditor";

export { TimelineEditor } from "./TimelineEditor";
export { ScrubbablePlayer } from "./ScrubbablePlayer";
export { TimelineBar } from "./TimelineBar";
export { ShotCard } from "./ShotCard";
export type * from "./types";

/**
 * Mở Trình chỉnh sửa timeline trong vùng mở rộng của Studio (không pop modal che màn hình).
 */
export function openTimelineEditor(episodeId?: string) {
  usePreview.getState().open({
    kind: "custom",
    title: episodeId ? `Trình chỉnh sửa timeline · ${episodeId}` : "Trình chỉnh sửa timeline",
    render: (close) => React.createElement(TimelineEditor, { episodeId, onClose: close }),
  });
}

