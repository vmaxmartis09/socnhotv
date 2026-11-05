"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { PlatformType, SocialAccount } from "@/lib/api/social";

interface AccountChipProps {
  account?: SocialAccount | {
    id: string;
    platform: PlatformType;
    display_name?: string;
    handle?: string;
    avatar?: string;
    status?: string;
  };
  size?: "sm" | "md";
  showPlatform?: boolean;
  selected?: boolean;
  className?: string;
  onClick?: () => void;
}

const PLATFORM_ICONS: Record<string, { label: string; bg: string; text: string }> = {
  youtube: { label: "YT", bg: "bg-red-500/10", text: "text-red-500" },
  tiktok: { label: "TT", bg: "bg-pink-500/10", text: "text-pink-400" },
  facebook: { label: "FB", bg: "bg-blue-500/10", text: "text-blue-500" },
  instagram: { label: "IG", bg: "bg-purple-500/10", text: "text-purple-400" },
  threads: { label: "TH", bg: "bg-zinc-500/10", text: "text-zinc-200" },
  x: { label: "X", bg: "bg-zinc-500/10", text: "text-zinc-200" },
  douyin: { label: "DY", bg: "bg-teal-500/10", text: "text-teal-400" },
};

export function AccountChip({
  account,
  size = "sm",
  showPlatform = true,
  selected = false,
  className,
  onClick,
}: AccountChipProps) {
  if (!account) return null;

  const platform = account.platform || "youtube";
  const pCfg = PLATFORM_ICONS[platform] || { label: platform.slice(0, 2).toUpperCase(), bg: "bg-zinc-800", text: "text-zinc-400" };
  const name = account.display_name || account.handle || account.id;
  const status = account.status || "manual";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border transition-all text-left select-none max-w-full truncate",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
        selected
          ? "border-primary bg-primary/10 text-primary shadow-sm"
          : "border-border bg-card/60 text-foreground hover:bg-accent hover:border-zinc-700",
        onClick ? "cursor-pointer" : "cursor-default",
        className
      )}
    >
      {/* Platform Badge / Avatar */}
      {account.avatar ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img decoding="async" loading="lazy"
          src={account.avatar}
          alt={name}
          className="w-4 h-4 rounded-full object-cover shrink-0"
        />
      ) : showPlatform ? (
        <span
          className={cn(
            "w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold shrink-0",
            pCfg.bg,
            pCfg.text
          )}
        >
          {pCfg.label}
        </span>
      ) : null}

      <span className="truncate font-medium">{name}</span>

      {/* Status Dot */}
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full shrink-0",
          status === "connected"
            ? "bg-emerald-500"
            : status === "expired"
            ? "bg-amber-500 animate-pulse"
            : status === "disabled"
            ? "bg-rose-500"
            : "bg-zinc-500"
        )}
        title={`Trạng thái: ${status}`}
      />
    </button>
  );
}
