"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { Character } from "@/lib/repositories";

/** Thẻ poster nhân vật dùng chung (tab Nhân vật, chi tiết Dự án…): ảnh lớn, tên và vai trò nằm trên ảnh. */
export function CharacterPoster({
  character: c,
  active = false,
  roleLabel,
  onClick,
}: {
  character: Character;
  active?: boolean;
  roleLabel: string;
  onClick: () => void;
}) {
  const img = c.referenceImages[0];
  return (
    <button
      type="button"
      aria-current={active}
      onClick={onClick}
      title={c.name}
      className={cn(
        "group relative block h-[168px] w-[124px] overflow-hidden rounded-2xl border-2 text-left transition-all active:scale-[0.98]",
        active ? "border-foreground" : "border-transparent opacity-80 hover:opacity-100"
      )}
    >
      {img ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={img} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover object-top transition-transform duration-300 group-hover:scale-105" />
      ) : (
        <span className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-accent to-muted text-5xl font-semibold text-muted-foreground/60">
          {c.name.replace("Bạn ", "").charAt(0)}
        </span>
      )}
      <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 via-black/35 to-transparent px-3 pb-2.5 pt-10 text-white">
        <span className="block truncate text-sm font-semibold">{c.name}</span>
        <span className="block truncate text-[11px] text-white/75 tnum">{roleLabel}</span>
      </span>
    </button>
  );
}
