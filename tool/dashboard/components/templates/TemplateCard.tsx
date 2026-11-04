"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { CORE_URL } from "@/lib/repositories/core";
import type { TemplateMeta } from "@/lib/api/video";
import { Film, Play } from "@/components/ui/icons";

export interface TemplateCardProps {
  template: TemplateMeta;
}

export function TemplateCard({ template }: TemplateCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const previewJpgUrl = `${CORE_URL}/video/templates/${template.id}/preview.jpg`;
  const previewMp4Url = `${CORE_URL}/video/templates/${template.id}/preview.mp4`;

  const handleMouseEnter = () => {
    setIsHovered(true);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  return (
    <Link
      href={`/templates/${template.id}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="group relative flex flex-col rounded-2xl border border-border bg-card p-3 transition-all duration-200 hover:-translate-y-1 hover:border-primary/50 hover:bg-accent/40 hover:shadow-xl hover:shadow-primary/5"
    >
      {/* Thumbnail / Video Container */}
      <div className="relative aspect-[9/16] w-full overflow-hidden rounded-xl bg-muted">
        <img
          src={previewJpgUrl}
          alt={template.name}
          className={`h-full w-full object-cover transition-opacity duration-300 ${
            isHovered ? "opacity-0" : "opacity-100"
          }`}
          onError={(e) => {
            // Fallback icon placeholder if preview image fails
            e.currentTarget.style.display = "none";
          }}
        />

        {/* Video preview on hover */}
        <video
          ref={videoRef}
          src={previewMp4Url}
          muted
          loop
          playsInline
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${
            isHovered ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        />

        {/* Badges Overlay */}
        <div className="absolute top-2.5 left-2.5 flex flex-wrap gap-1.5 z-10">
          <span className="rounded-full bg-background/80 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-primary backdrop-blur-md border border-primary/20">
            {template.category}
          </span>
        </div>

        <div className="absolute bottom-2.5 right-2.5 z-10">
          <span className="rounded-full bg-background/80 px-2 py-0.5 text-[11px] font-medium text-foreground backdrop-blur-sm border border-border">
            {template.duration.min}s - {template.duration.max}s
          </span>
        </div>
      </div>

      {/* Meta Info */}
      <div className="mt-3 flex flex-col gap-1">
        <h3 className="line-clamp-1 text-sm font-bold text-foreground group-hover:text-primary transition-colors">
          {template.name}
        </h3>

        {/* Platform Icons */}
        <div className="mt-1 flex flex-wrap gap-1">
          {template.platforms.map((plat) => (
            <span
              key={plat}
              className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase text-muted-foreground"
            >
              {plat}
            </span>
          ))}
        </div>
      </div>
    </Link>
  );
}
