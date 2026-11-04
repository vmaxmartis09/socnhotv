"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { PlatformType } from "@/lib/api/social";
import {
  Bookmark,
  Heart,
  MessageCircle,
  Music,
  Share2,
  Video,
} from "lucide-react";

interface PhonePreviewProps {
  platform: PlatformType;
  title: string;
  caption: string;
  hashtags?: string[];
  accountHandle?: string;
  accountAvatar?: string;
  videoThumb?: string;
  productLink?: string;
}

export function PhonePreview({
  platform,
  title,
  caption,
  hashtags = [],
  accountHandle = "@socnhotv.official",
  accountAvatar,
  videoThumb,
  productLink,
}: PhonePreviewProps) {
  const [expanded, setExpanded] = useState(false);

  const fullText = [caption, hashtags.join(" ")].filter(Boolean).join("\n\n");
  const isLong = fullText.length > 80;
  const displayText = !expanded && isLong ? `${fullText.slice(0, 80)}...` : fullText;

  return (
    <div className="flex flex-col items-center select-none">
      {/* Outer Phone Shell */}
      <div className="relative w-[280px] h-[520px] rounded-[36px] bg-neutral-950 p-2.5 shadow-2xl ring-1 ring-neutral-800 border-4 border-neutral-900 overflow-hidden flex flex-col justify-between text-white">
        {/* Dynamic Island / Speaker Notch */}
        <div className="absolute top-3.5 left-1/2 -translate-x-1/2 z-30 h-4 w-24 rounded-full bg-black/90 flex items-center justify-center">
          <div className="h-2 w-2 rounded-full bg-neutral-800 mr-2" />
          <div className="h-1.5 w-8 rounded-full bg-neutral-900" />
        </div>

        {/* Video / Background Layer */}
        <div className="absolute inset-0 z-0 bg-neutral-900 overflow-hidden flex items-center justify-center">
          {videoThumb ? (
            <img
              src={`/api/media?path=${encodeURIComponent(videoThumb)}`}
              alt="Preview"
              className="h-full w-full object-cover"
              onError={(e) => {
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-neutral-600 gap-2 p-4 text-center">
              <Video className="h-10 w-10 stroke-[1.5]" />
              <span className="text-[11px] font-medium">Khung hình 9:16</span>
            </div>
          )}
          {/* Subtle gradient vignette at bottom for caption legibility */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/90 pointer-events-none" />
        </div>

        {/* Top Status & Platform Header */}
        <div className="relative z-20 pt-4 px-3 flex items-center justify-between text-[11px] font-semibold text-white/90">
          <span className="uppercase tracking-wider text-[10px] bg-black/40 backdrop-blur-md px-2 py-0.5 rounded-full border border-white/10">
            {platform}
          </span>
          <span className="text-white/60 text-[10px]">Đang theo dõi</span>
        </div>

        {/* Right Action Rail (TikTok / Shorts / Reels style) */}
        <div className="relative z-20 self-end mr-1 space-y-3 flex flex-col items-center text-white/90">
          {/* Avatar button */}
          <div className="relative h-9 w-9 rounded-full border-2 border-white bg-primary flex items-center justify-center overflow-hidden">
            {accountAvatar ? (
              <img src={accountAvatar} alt="Avatar" className="h-full w-full object-cover" />
            ) : (
              <span className="text-xs font-bold text-white uppercase">{accountHandle.slice(1, 3)}</span>
            )}
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 h-3 w-3 rounded-full bg-rose-500 flex items-center justify-center text-[9px] font-bold">
              +
            </div>
          </div>

          {/* Like */}
          <div className="flex flex-col items-center gap-0.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black/30 backdrop-blur-md">
              <Heart className="h-4 w-4 fill-white/80" />
            </div>
            <span className="text-[10px] font-medium">12.4K</span>
          </div>

          {/* Comment */}
          <div className="flex flex-col items-center gap-0.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black/30 backdrop-blur-md">
              <MessageCircle className="h-4 w-4 fill-white/80" />
            </div>
            <span className="text-[10px] font-medium">358</span>
          </div>

          {/* Bookmark */}
          <div className="flex flex-col items-center gap-0.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black/30 backdrop-blur-md">
              <Bookmark className="h-4 w-4 fill-white/80" />
            </div>
            <span className="text-[10px] font-medium">1.2K</span>
          </div>

          {/* Share */}
          <div className="flex flex-col items-center gap-0.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black/30 backdrop-blur-md">
              <Share2 className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-medium">Chia sẻ</span>
          </div>

          {/* Rotating vinyl disk */}
          <div className="h-7 w-7 rounded-full bg-neutral-900 border-2 border-neutral-700 flex items-center justify-center animate-spin">
            <Music className="h-3 w-3 text-white/70" />
          </div>
        </div>

        {/* Bottom Overlay: Handle + Caption */}
        <div className="relative z-20 pb-4 px-3 space-y-1.5 max-w-[210px]">
          <p className="font-bold text-xs text-white drop-shadow-md">
            {accountHandle}
          </p>

          {/* Truncated caption with 'xem thêm' */}
          <div className="text-[11px] leading-relaxed text-white/90 drop-shadow">
            <p className="whitespace-pre-line">
              {displayText}
              {isLong && !expanded && (
                <button
                  type="button"
                  onClick={() => setExpanded(true)}
                  className="font-bold text-white ml-1 hover:underline cursor-pointer"
                >
                  …xem thêm
                </button>
              )}
            </p>
            {expanded && isLong && (
              <button
                type="button"
                onClick={() => setExpanded(false)}
                className="text-[10px] text-white/70 block mt-1 hover:underline cursor-pointer"
              >
                Ẩn bớt
              </button>
            )}
          </div>

          {/* Product link badge if affiliate */}
          {productLink && (
            <div className="flex items-center gap-1 bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-md text-[10px] font-medium">
              <span>🛒 Sản phẩm gắn kèm</span>
            </div>
          )}

          {/* Sound bar */}
          <div className="flex items-center gap-1.5 text-[10px] text-white/70 pt-0.5">
            <Music className="h-3 w-3 shrink-0" />
            <span className="truncate">Âm thanh gốc - Sóc Nhỏ TV</span>
          </div>
        </div>
      </div>

      <span className="text-[10px] text-muted-foreground mt-2">
        Mô phỏng hiển thị trên {platform}
      </span>
    </div>
  );
}
