"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { usePreview, type PreviewItem } from "@/lib/preview";
import { useStudioStore } from "@/store";
import { Markdown } from "@/components/project/Markdown";
import { fetchText } from "@/lib/repositories/library";
import { ChevronRight, X, Users, Film, FolderGit2 } from "@/components/ui/icons";

/** Vùng xem trước mở rộng sang trái của panel: ảnh, video, Markdown, tóm tắt dự án. */
export function PreviewPane({ item }: { item: PreviewItem }) {
  const { go, close } = usePreview();
  const { projects, activeProjectId } = useStudioStore();
  const [text, setText] = useState("");

  const url = item.kind === "markdown" ? item.url : undefined;
  useEffect(() => {
    if (item.kind !== "markdown") return;
    if (item.text !== undefined) return setText(item.text);
    if (url) fetchText(url).then(setText).catch(() => setText(""));
  }, [item, url]);

  const media = item.kind === "image" || item.kind === "video" ? item : null;
  const cur = media?.items[media.index];

  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex h-11 shrink-0 items-center gap-2 border-b border-border px-3">
        <span className="min-w-0 flex-1 truncate text-[13px] font-semibold text-foreground" title={item.title}>
          {item.title}
        </span>
        {media && media.items.length > 1 && (
          <>
            <button type="button" title="Trước" aria-label="Trước" onClick={() => go((media.index - 1 + media.items.length) % media.items.length)} className="flex h-7 w-7 items-center justify-center rounded-full border border-border active:scale-90">
              <ChevronRight className="h-4 w-4 rotate-180" />
            </button>
            <span className="text-xs text-muted-foreground tnum">{media.index + 1}/{media.items.length}</span>
            <button type="button" title="Sau" aria-label="Sau" onClick={() => go((media.index + 1) % media.items.length)} className="flex h-7 w-7 items-center justify-center rounded-full border border-border active:scale-90">
              <ChevronRight className="h-4 w-4" />
            </button>
          </>
        )}
        <button type="button" title="Đóng xem trước (Esc)" aria-label="Đóng xem trước" onClick={close} className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground hover:bg-accent active:scale-90">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="scroll-quiet min-h-0 flex-1 overflow-y-auto p-4">
        {media && cur && (
          <motion.div key={cur.url} initial={false} animate={{ opacity: 1, scale: 1 }} className="flex h-full flex-col items-center justify-center gap-2">
            {media.kind === "video" ? (
              <video src={cur.url} controls autoPlay className="max-h-full max-w-full rounded-xl bg-black" />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={cur.url} alt={cur.name} className="max-h-full max-w-full rounded-xl object-contain" />
            )}
            <span className="text-xs text-muted-foreground">{cur.name}</span>
          </motion.div>
        )}

        {item.kind === "custom" && item.render(close)}

        {item.kind === "markdown" && (
          <article className="rounded-xl border border-border bg-card p-5">
            <Markdown>{text || "…"}</Markdown>
          </article>
        )}

        {item.kind === "project" && (() => {
          const p = projects.find((x) => x.id === item.projectId);
          if (!p) return null;
          return (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent"><FolderGit2 className="h-6 w-6" /></span>
                <div className="min-w-0">
                  <p className="truncate text-lg font-semibold">{p.name}</p>
                  <p className="text-xs text-muted-foreground">{p.id}{p.id === activeProjectId ? " · đang mở" : ""}</p>
                </div>
              </div>
              <p className="text-[13px] leading-relaxed text-muted-foreground">{p.description || "—"}</p>
              <dl className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl border border-border p-3"><Users className="mx-auto h-4 w-4 text-muted-foreground" /><dd className="mt-1 text-lg font-semibold tnum">{p.charactersCount}</dd></div>
                <div className="rounded-xl border border-border p-3"><Film className="mx-auto h-4 w-4 text-muted-foreground" /><dd className="mt-1 text-lg font-semibold tnum">{p.episodesCount}</dd></div>
                <div className="rounded-xl border border-border p-3"><dt className="text-[11px] text-muted-foreground">Tỉ lệ</dt><dd className="mt-1 text-lg font-semibold tnum">{p.defaultAspectRatio}</dd></div>
              </dl>
              <p className="text-xs text-muted-foreground">Nhấn đúp để vào dự án.</p>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
