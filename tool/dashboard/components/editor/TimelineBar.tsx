"use client";

import React from "react";
import type { ShotItem } from "./types";
import { cn } from "@/lib/utils";

interface TimelineBarProps {
  shots: ShotItem[];
  totalDurationSec: number;
  currentTimeSec: number;
  selectedShotId: string | null;
  onSelectShot: (shotId: string) => void;
  onSeek: (timeSec: number) => void;
}

export function TimelineBar({
  shots,
  totalDurationSec,
  currentTimeSec,
  selectedShotId,
  onSelectShot,
  onSeek,
}: TimelineBarProps) {
  const safeTotal = Math.max(1, totalDurationSec);

  const handleBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    onSeek(ratio * safeTotal);
  };

  return (
    <div className="relative flex flex-col gap-1 w-full select-none">
      {/* Time markers bar */}
      <div className="flex justify-between text-[10px] text-muted-foreground font-mono px-1">
        <span>00:00</span>
        <span>
          {Math.floor(safeTotal / 60)}:
          {String(Math.floor(safeTotal % 60)).padStart(2, "0")}
        </span>
      </div>

      {/* Main interactive timeline track */}
      <div
        onClick={handleBarClick}
        className="relative h-10 w-full rounded-lg bg-secondary/50 border border-border/80 overflow-hidden cursor-pointer flex"
      >
        {shots.map((shot) => {
          const widthPct = shot.enabled
            ? (shot.durationSec / safeTotal) * 100
            : 0;
          if (widthPct <= 0) return null;

          const isSelected = selectedShotId === shot.shotId;
          const isPriority1 = shot.priority === 1;

          return (
            <div
              key={shot.shotId}
              onClick={(e) => {
                e.stopPropagation();
                onSelectShot(shot.shotId);
                onSeek(shot.startSec);
              }}
              style={{ width: `${widthPct}%` }}
              className={cn(
                "relative h-full border-r border-background/40 px-1 py-0.5 flex flex-col justify-between transition-colors",
                isSelected
                  ? "bg-primary/30 text-primary-foreground font-bold ring-2 ring-primary ring-inset"
                  : isPriority1
                  ? "bg-amber-500/20 hover:bg-amber-500/30 text-amber-300"
                  : "bg-muted/60 hover:bg-muted text-muted-foreground",
                shot.isModified && "border-b-2 border-b-cyan-400"
              )}
              title={`${shot.shotId}: ${shot.title} (${shot.durationSec}s)`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono leading-none truncate">
                <span className="font-semibold">{shot.shotId}</span>
                <span className="opacity-75">{shot.durationSec}s</span>
              </div>
              <div className="text-[9px] truncate opacity-90">
                {shot.speaker}
              </div>
            </div>
          );
        })}

        {/* Playhead scrub indicator */}
        <div
          style={{
            left: `${Math.min(100, (currentTimeSec / safeTotal) * 100)}%`,
          }}
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10 pointer-events-none transition-all duration-75 shadow-[0_0_8px_rgba(239,68,68,0.8)]"
        >
          <div className="absolute -top-1 -left-1.5 w-3.5 h-3.5 bg-red-500 rounded-full shadow border-2 border-white" />
        </div>
      </div>
    </div>
  );
}
