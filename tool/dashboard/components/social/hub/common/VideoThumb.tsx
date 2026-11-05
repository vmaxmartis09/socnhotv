"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Film } from "@/components/ui/icons";

interface VideoThumbProps {
  thumb?: string;
  projectId?: string;
  title?: string;
  durationSec?: number;
  aspectRatio?: string;
  className?: string;
  aspectClassName?: string;
  onClick?: () => void;
}

export function VideoThumb({
  thumb,
  projectId = "soc-nho-tv",
  title = "",
  durationSec,
  aspectRatio = "9:16",
  className,
  aspectClassName,
  onClick,
}: VideoThumbProps) {
  // Build thumbnail src
  let src = "";
  if (thumb) {
    if (thumb.startsWith("http://") || thumb.startsWith("https://") || thumb.startsWith("data:")) {
      src = thumb;
    } else {
      const clean = thumb.startsWith("/") ? thumb.slice(1) : thumb;
      src = `/core/projects/${projectId}/files/${clean}`;
    }
  }

  const formatDuration = (sec?: number) => {
    if (!sec || sec <= 0) return null;
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const durStr = formatDuration(durationSec);

  return (
    <div
      onClick={onClick}
      className={cn(
        "relative rounded-lg overflow-hidden bg-zinc-900 border border-zinc-800 flex items-center justify-center shrink-0 group select-none",
        aspectClassName || "aspect-[9/16] w-20",
        onClick && "cursor-pointer hover:border-zinc-700 transition-all",
        className
      )}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img decoding="async" loading="lazy"
          src={src}
          alt={title || "Video thumbnail"}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          onError={(e) => {
            // fallback if image not found
            (e.target as HTMLElement).style.display = "none";
          }}
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-2 bg-gradient-to-br from-zinc-800 to-zinc-950 text-zinc-500">
          <Film className="w-5 h-5 opacity-40 mb-1" />
          <span className="text-[9px] text-center line-clamp-1 opacity-60">
            {title || "Video"}
          </span>
        </div>
      )}

      {/* Badges Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />

      {aspectRatio && (
        <span className="absolute top-1 left-1 px-1 py-0.2 rounded bg-black/60 backdrop-blur-sm text-[9px] font-mono text-zinc-300 pointer-events-none">
          {aspectRatio}
        </span>
      )}

      {durStr && (
        <span className="absolute bottom-1 right-1 px-1 py-0.2 rounded bg-black/70 backdrop-blur-sm text-[10px] font-mono font-medium text-white pointer-events-none">
          {durStr}
        </span>
      )}
    </div>
  );
}
