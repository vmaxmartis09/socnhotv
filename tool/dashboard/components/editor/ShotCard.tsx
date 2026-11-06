"use client";

import React, { useState } from "react";
import type { ShotItem } from "./types";
import { CORE_URL } from "@/lib/repositories/core";
import {
  ArrowUp,
  ArrowDown,
  Eye,
  EyeOff,
  Edit3,
  RotateCcw,
  Film,
  Camera,
  Image as ImageIcon,
} from "./icons";
import { cn } from "@/lib/utils";

interface ShotCardProps {
  shot: ShotItem;
  index: number;
  totalShots: number;
  isSelected: boolean;
  onSelect: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onToggle: (enabled: boolean) => void;
  onDurationChange: (durSec: number) => void;
  onMediaChange: (mediaSrc: string) => void;
  onSubtitleChange: (sub: string) => void;
  onReset: () => void;
  isEn?: boolean;
}

export function ShotCard({
  shot,
  index,
  totalShots,
  isSelected,
  onSelect,
  onMoveUp,
  onMoveDown,
  onToggle,
  onDurationChange,
  onMediaChange,
  onSubtitleChange,
  onReset,
  isEn = false,
}: ShotCardProps) {
  const [isEditingMedia, setIsEditingMedia] = useState(false);
  const [customMedia, setCustomMedia] = useState(shot.mediaSrc);
  const [isEditingSub, setIsEditingSub] = useState(false);
  const [tempSub, setTempSub] = useState(shot.subtitle || shot.dialogue);

  const priorityColor =
    shot.priority === 1
      ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
      : shot.priority === 2
      ? "bg-blue-500/10 text-blue-500 border-blue-500/30"
      : "bg-muted text-muted-foreground border-border";

  return (
    <div
      onClick={onSelect}
      className={cn(
        "relative rounded-xl border p-3.5 transition-all cursor-pointer flex flex-col gap-3",
        isSelected
          ? "border-primary bg-primary/[0.03] ring-1 ring-primary shadow-sm"
          : "border-border bg-card hover:border-border/80 hover:bg-muted/30",
        !shot.enabled && "opacity-55 grayscale-[40%]",
        shot.isModified && "border-l-4 border-l-cyan-500"
      )}
    >
      {/* Top Header: Shot ID, Title, Status, Action buttons */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono font-bold text-sm bg-secondary px-2 py-0.5 rounded text-foreground">
            {shot.shotId}
          </span>
          <span
            className={cn(
              "text-[10px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider",
              priorityColor
            )}
          >
            P{shot.priority}
          </span>
          {shot.isModified && (
            <span className="text-[10px] bg-cyan-500/10 text-cyan-500 border border-cyan-500/30 px-1.5 py-0.5 rounded font-mono">
              {isEn ? "MODIFIED" : "ĐÃ SỬA"}
            </span>
          )}
          <span className="text-xs text-muted-foreground truncate font-medium">
            {shot.speaker} · {shot.title}
          </span>
        </div>

        {/* Action Controls: Move Up/Down, Enable/Disable, Reset */}
        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onMoveUp}
            disabled={index === 0}
            className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground disabled:opacity-30"
            title={isEn ? "Move Up" : "Lên trên"}
          >
            <ArrowUp className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onMoveDown}
            disabled={index === totalShots - 1}
            className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground disabled:opacity-30"
            title={isEn ? "Move Down" : "Xuống dưới"}
          >
            <ArrowDown className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onToggle(!shot.enabled)}
            className={cn(
              "p-1 rounded hover:bg-secondary transition-colors",
              shot.enabled ? "text-emerald-500" : "text-muted-foreground"
            )}
            title={shot.enabled ? (isEn ? "Disable shot" : "Tắt shot này") : (isEn ? "Enable shot" : "Bật shot này")}
          >
            {shot.enabled ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          </button>
          {shot.isModified && (
            <button
              onClick={onReset}
              className="p-1 rounded hover:bg-secondary text-amber-500 hover:text-amber-400"
              title={isEn ? "Reset this shot to base script" : "Đặt lại shot về kịch bản gốc"}
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Middle row: Media thumbnail + Timing + Camera */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-center">
        {/* Media Preview Box */}
        <div className="relative aspect-video rounded-lg bg-secondary/60 border border-border/80 overflow-hidden flex items-center justify-center">
          {shot.mediaSrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              loading="lazy"
              decoding="async"
              src={
                shot.mediaSrc.startsWith("http")
                  ? shot.mediaSrc
                  : `${CORE_URL}/data/projects/${shot.mediaSrc}`
              }
              alt={shot.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-muted-foreground text-[10px]">
              <ImageIcon className="w-4 h-4 mb-1 opacity-60" />
              <span>{isEn ? "No image" : "Chưa có ảnh"}</span>
            </div>
          )}
          <span className="absolute bottom-1 right-1 bg-black/60 text-white font-mono text-[9px] px-1 rounded">
            {shot.durationSec}s
          </span>
        </div>

        {/* Controls: Duration & Camera & Media Path */}
        <div className="col-span-3 flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-4 text-xs">
            {/* Duration Input */}
            <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
              <span className="text-muted-foreground font-medium">
                {isEn ? "Duration:" : "Thời lượng:"}
              </span>
              <input
                type="number"
                min={0.5}
                max={120}
                step={0.5}
                value={shot.durationSec}
                onChange={(e) => onDurationChange(parseFloat(e.target.value) || 1.0)}
                className="w-16 px-2 py-1 text-center font-mono text-xs rounded border border-border bg-background focus:ring-1 focus:ring-primary"
              />
              <span className="text-muted-foreground font-mono">s</span>
              <span className="text-[11px] text-muted-foreground font-mono ml-2">
                ({shot.startSec}s - {shot.endSec}s)
              </span>
            </div>

            {/* Camera badge */}
            <div className="flex items-center gap-1 text-[11px] font-mono text-muted-foreground bg-muted/50 px-2 py-0.5 rounded border border-border">
              <Camera className="w-3 h-3 text-primary" />
              <span>{shot.camera || "push-in"}</span>
            </div>
          </div>

          {/* Media source editor */}
          <div className="flex items-center gap-2 text-xs" onClick={(e) => e.stopPropagation()}>
            <Film className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
            {isEditingMedia ? (
              <div className="flex items-center gap-1.5 flex-1">
                <input
                  type="text"
                  value={customMedia}
                  onChange={(e) => setCustomMedia(e.target.value)}
                  placeholder="content/episodes/ep01/.../S01.mp4"
                  className="flex-1 px-2 py-1 text-xs rounded border border-border bg-background font-mono"
                />
                <button
                  onClick={() => {
                    onMediaChange(customMedia);
                    setIsEditingMedia(false);
                  }}
                  className="px-2 py-1 text-xs rounded bg-primary text-primary-foreground font-medium"
                >
                  OK
                </button>
                <button
                  onClick={() => setIsEditingMedia(false)}
                  className="px-2 py-1 text-xs rounded bg-muted text-muted-foreground"
                >
                  {isEn ? "Cancel" : "Hủy"}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-muted-foreground font-mono text-[11px] truncate flex-1">
                  {shot.mediaSrc || (isEn ? "(Default from flow)" : "(Mặc định từ flow)")}
                </span>
                <button
                  onClick={() => setIsEditingMedia(true)}
                  className="text-[11px] text-primary hover:underline font-medium shrink-0"
                >
                  {isEn ? "Change media" : "Thay ảnh/clip"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Subtitle / Dialogue Live Edit */}
      <div className="flex flex-col gap-1 text-xs" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium flex items-center gap-1">
            <Edit3 className="w-3 h-3" />
            {isEn ? "Subtitle & Dialogue:" : "Phụ đề & Lời thoại:"}
          </span>
          {!isEditingSub ? (
            <button
              onClick={() => setIsEditingSub(true)}
              className="text-[11px] text-primary hover:underline font-medium"
            >
              {isEn ? "Edit text" : "Sửa chữ"}
            </button>
          ) : (
            <div className="flex gap-1.5">
              <button
                onClick={() => {
                  onSubtitleChange(tempSub);
                  setIsEditingSub(false);
                }}
                className="text-[11px] text-primary font-bold hover:underline"
              >
                {isEn ? "Save text" : "Lưu chữ"}
              </button>
              <button
                onClick={() => {
                  setTempSub(shot.subtitle || shot.dialogue);
                  setIsEditingSub(false);
                }}
                className="text-[11px] text-muted-foreground hover:underline"
              >
                {isEn ? "Cancel" : "Hủy"}
              </button>
            </div>
          )}
        </div>

        {isEditingSub ? (
          <textarea
            value={tempSub}
            onChange={(e) => setTempSub(e.target.value)}
            rows={2}
            className="w-full p-2 text-xs rounded-lg border border-border bg-background focus:ring-1 focus:ring-primary leading-relaxed"
          />
        ) : (
          <p className="text-foreground/90 bg-muted/30 p-2 rounded-lg border border-border/50 text-[12px] leading-relaxed italic">
            "{shot.subtitle || shot.dialogue || (isEn ? "No dialogue" : "Không có thoại")}"
          </p>
        )}
      </div>
    </div>
  );
}
