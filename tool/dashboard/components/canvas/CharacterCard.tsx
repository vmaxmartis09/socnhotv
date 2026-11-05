"use client";

import React from "react";
import type { Character } from "@/lib/repositories";

/** Thẻ nhân vật trong node: ảnh chính, thư viện ảnh, thông số, tính cách, câu cửa miệng, nghe thử giọng. */
export function CharacterCard({ character: c }: { character: Character }) {
  const gallery = c.referenceImages.slice(1, 6);
  return (
    <div className="space-y-2 rounded border border-border bg-muted/20 p-2">
      <div className="flex gap-2.5">
        {c.referenceImages[0] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img decoding="async" loading="lazy"
            src={c.referenceImages[0]}
            alt={c.name}
            className="h-20 w-20 shrink-0 rounded border border-border object-cover object-top"
          />
        ) : (
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded border border-border bg-accent text-lg font-semibold text-muted-foreground">
            {c.name.replace("Bạn ", "").charAt(0)}
          </div>
        )}
        <div className="min-w-0 flex-1 text-[13px]">
          <p className="truncate text-xs font-semibold text-foreground">{c.name}</p>
          <p className="text-muted-foreground">
            {c.role === "main" ? "Nhân vật chính" : "Nhân vật phụ"}
          </p>
          <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
            <dt className="text-muted-foreground">Cao</dt>
            <dd className="tnum font-medium text-foreground">
              {c.heightCm} cm · {c.scaleRatio}x
            </dd>
            <dt className="text-muted-foreground">Giọng</dt>
            <dd className="truncate font-medium text-foreground">
              {c.voiceId || "—"} · {c.defaultTempo ?? 1}x
            </dd>
          </dl>
        </div>
      </div>

      {gallery.length > 0 && (
        <div className="flex gap-1 overflow-hidden">
          {gallery.map((u) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img decoding="async"
              key={u}
              src={u}
              alt=""
              loading="lazy"
              className="h-9 w-9 rounded border border-border object-cover object-top"
            />
          ))}
          {c.referenceImages.length > 6 && (
            <span className="flex h-9 w-9 items-center justify-center rounded border border-border text-xs text-muted-foreground tnum">
              +{c.referenceImages.length - 6}
            </span>
          )}
        </div>
      )}

      {c.memory.personality && (
        <p className="line-clamp-2 text-[13px] text-muted-foreground">
          <span className="font-medium text-foreground">Tính cách: </span>
          {c.memory.personality}
        </p>
      )}
      {c.memory.catchphrases.length > 0 && (
        <p className="line-clamp-1 text-[13px] italic text-muted-foreground">
          “{c.memory.catchphrases[0]}”
        </p>
      )}
      {(c.description || c.promptLock) && (
        <p className="line-clamp-2 text-[13px] text-muted-foreground">
          {c.description || c.promptLock}
        </p>
      )}
      {c.sampleAudioUrl && (
        <audio
          controls
          preload="none"
          src={c.sampleAudioUrl}
          className="nodrag nowheel h-7 w-full"
        />
      )}
    </div>
  );
}
