"use client";

import React, { useRef, useState, useEffect } from "react";
import { CORE_URL } from "@/lib/repositories/core";
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Sparkles,
} from "./icons";
import { cn } from "@/lib/utils";
import type { ShotItem } from "./types";

interface ScrubbablePlayerProps {
  videoUrl: string | null;
  thumbUrl: string | null;
  totalDurationSec: number;
  activeShot: ShotItem | null;
  currentTimeSec: number;
  onTimeUpdate: (sec: number) => void;
  aspect?: string;
  isEn?: boolean;
}

export function ScrubbablePlayer({
  videoUrl,
  thumbUrl,
  totalDurationSec,
  activeShot,
  currentTimeSec,
  onTimeUpdate,
  aspect = "16:9",
  isEn = false,
}: ScrubbablePlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showSafeZone, setShowSafeZone] = useState(true);

  const fullVideoSrc = videoUrl
    ? (videoUrl.startsWith("http") ? videoUrl : `${CORE_URL}${videoUrl.startsWith("/") ? "" : "/"}${videoUrl}`)
    : null;

  // Đồng bộ seek từ ngoài vào video tag
  useEffect(() => {
    if (videoRef.current && Math.abs(videoRef.current.currentTime - currentTimeSec) > 0.5) {
      videoRef.current.currentTime = currentTimeSec;
    }
  }, [currentTimeSec]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    onTimeUpdate(videoRef.current.currentTime);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    onTimeUpdate(val);
    if (videoRef.current) {
      videoRef.current.currentTime = val;
    }
  };

  const fmtTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  const isWide = !aspect.includes("9:16");

  return (
    <div className="flex flex-col gap-2 w-full bg-card rounded-xl border border-border p-3 shadow-sm">
      {/* Khung hiển thị Video / Visual Frame */}
      <div
        className={cn(
          "relative mx-auto w-full bg-black rounded-lg overflow-hidden flex items-center justify-center",
          isWide ? "aspect-video max-h-[380px]" : "aspect-[9/16] max-h-[460px]"
        )}
      >
        {fullVideoSrc ? (
          <video
            ref={videoRef}
            src={fullVideoSrc}
            poster={thumbUrl ? `${CORE_URL}${thumbUrl.startsWith("/") ? "" : "/"}${thumbUrl}` : undefined}
            onTimeUpdate={handleTimeUpdate}
            onEnded={() => setIsPlaying(false)}
            muted={isMuted}
            playsInline
            preload="metadata"
            className="w-full h-full object-contain"
          />
        ) : (
          /* Khi chưa có video thành phẩm: hiển thị preview shot trực quan */
          <div className="relative w-full h-full flex items-center justify-center bg-zinc-950">
            {activeShot?.mediaSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                loading="lazy"
                decoding="async"
                src={
                  activeShot.mediaSrc.startsWith("http")
                    ? activeShot.mediaSrc
                    : `${CORE_URL}/data/projects/${activeShot.mediaSrc}`
                }
                alt={activeShot.title}
                className="w-full h-full object-contain opacity-85"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = "none";
                }}
              />
            ) : (
              <div className="text-center p-6 space-y-2">
                <Sparkles className="w-8 h-8 text-amber-400 mx-auto opacity-80" />
                <p className="text-sm font-medium text-foreground">
                  {activeShot ? `${activeShot.shotId}: ${activeShot.title}` : (isEn ? "Ready to preview" : "Sẵn sàng xem trước")}
                </p>
                <p className="text-xs text-muted-foreground">
                  {isEn ? "Render to preview assembled video" : "Bấm 'Render lại' để tạo video hoàn chỉnh"}
                </p>
              </div>
            )}

            {/* Subtitle overlay preview trực tiếp trên frame */}
            {activeShot && activeShot.subtitle && (
              <div className="absolute bottom-8 inset-x-4 flex justify-center pointer-events-none">
                <div className="bg-black/75 backdrop-blur-sm border border-white/20 text-white text-xs md:text-sm px-3.5 py-1.5 rounded-full shadow-lg font-medium max-w-[85%] text-center">
                  {activeShot.subtitle}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Safe Zone guide overlay */}
        {showSafeZone && (
          <div className="absolute inset-0 pointer-events-none border border-emerald-500/30 m-[5%] rounded-md">
            <div className="absolute inset-0 border border-dashed border-amber-400/40 m-[5%]">
              <span className="absolute top-1 left-1.5 text-[9px] font-mono text-amber-400/75 bg-black/60 px-1 rounded">
                Safe Zone (Action 90% / Title 80%)
              </span>
            </div>
          </div>
        )}

        {/* Shot tag indicator ở góc trên */}
        {activeShot && (
          <div className="absolute top-2.5 left-2.5 bg-black/70 backdrop-blur border border-white/10 text-white text-[10px] font-mono px-2 py-0.5 rounded shadow">
            {activeShot.shotId} · {activeShot.durationSec}s · {activeShot.speaker}
          </div>
        )}
      </div>

      {/* Control bar: Scrub slider & Buttons */}
      <div className="flex flex-col gap-1.5 pt-1">
        {/* Scrub Slider */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-foreground font-medium w-11 text-right">
            {fmtTime(currentTimeSec)}
          </span>
          <input
            type="range"
            min={0}
            max={Math.max(1, totalDurationSec)}
            step={0.1}
            value={currentTimeSec}
            onChange={handleSliderChange}
            className="flex-1 h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
          />
          <span className="text-xs font-mono text-muted-foreground w-11">
            {fmtTime(totalDurationSec)}
          </span>
        </div>

        {/* Playback Buttons */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => {
                onTimeUpdate(0);
                if (videoRef.current) videoRef.current.currentTime = 0;
              }}
              className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title={isEn ? "Rewind to beginning" : "Về đầu"}
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={togglePlay}
              className="p-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
              title={isPlaying ? (isEn ? "Pause" : "Tạm dừng") : (isEn ? "Play" : "Phát")}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title={isMuted ? (isEn ? "Unmute" : "Bật tiếng") : (isEn ? "Mute" : "Tắt tiếng")}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSafeZone(!showSafeZone)}
              className={cn(
                "text-[11px] px-2 py-1 rounded border transition-colors font-mono",
                showSafeZone
                  ? "bg-amber-500/10 border-amber-500/40 text-amber-500 dark:text-amber-400"
                  : "bg-muted border-border text-muted-foreground"
              )}
            >
              Safe Zone
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
