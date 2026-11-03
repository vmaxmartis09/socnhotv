"use client";

import { enterOnce } from "@/lib/motion";
import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Markdown } from "./Markdown";
import { fetchText, type LibraryEpisode, type ProjectLibrary } from "@/lib/repositories/library";
import { ChevronRight, Film, ScrollText, Video, Images, Play } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

/** Xem một tập: phim hoàn chỉnh, các phiên bản, cảnh quay, ảnh và kịch bản (Markdown). */
export function EpisodeDetail({
  episode,
  lib,
  onBack,
}: {
  episode: LibraryEpisode;
  lib: ProjectLibrary;
  onBack: () => void;
}) {
  const videos = useMemo(() => lib.videos.filter((v) => v.episodeId === episode.id), [lib, episode.id]);
  const images = useMemo(() => lib.images.filter((v) => v.episodeId === episode.id), [lib, episode.id]);
  const scripts = useMemo(() => lib.scripts.filter((s) => s.episodeId === episode.id), [lib, episode.id]);

  const finals = videos.filter((v) => !v.name.includes("/"));
  const scenes = videos.filter((v) => v.name.includes("/"));
  const [current, setCurrent] = useState<string | undefined>(finals[0]?.url ?? scenes[0]?.url);
  const [scriptIdx, setScriptIdx] = useState(0);
  const [text, setText] = useState("");

  useEffect(() => {
    const s = scripts[scriptIdx];
    if (!s) return setText("");
    fetchText(s.url).then(setText).catch(() => setText(s.preview));
  }, [scripts, scriptIdx]);

  const shortName = (n: string) => n.replace(/^soc_bi_kham_rang_/, "").replace(/\.mp4$/, "");

  return (
    <motion.div initial={enterOnce(`ep:${episode.id}`, { opacity: 0, x: 16 })} animate={{ opacity: 1, x: 0 }} className="space-y-4">
      <div className="flex items-center gap-2">
        <button type="button" onClick={onBack} title="Quay lại" aria-label="Quay lại" className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-transform hover:text-foreground active:scale-90">
          <ChevronRight className="h-4 w-4 rotate-180" />
        </button>
        <Film className="h-4 w-4 text-brand" />
        <h2 className="min-w-0 flex-1 truncate text-base font-semibold text-foreground">{episode.title}</h2>
      </div>

      {current ? (
        <video key={current} src={current} controls className="mx-auto max-h-[52vh] w-full rounded-xl bg-black" />
      ) : (
        <p className="py-8 text-center text-sm text-muted-foreground">Chưa có video</p>
      )}

      {finals.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          {finals.map((v) => (
            <button key={v.id} type="button" onClick={() => setCurrent(v.url)} title={v.name} className={cn("flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs transition-colors", current === v.url ? "border-foreground bg-foreground text-background" : "border-border text-muted-foreground hover:text-foreground")}>
              <Play className="h-3 w-3" />
              {shortName(v.name)}
            </button>
          ))}
        </div>
      )}

      {scenes.length > 0 && (
        <section className="space-y-2">
          <h3 className="flex items-center gap-1.5 text-[13px] font-semibold"><Video className="h-4 w-4 text-muted-foreground" />{scenes.length}</h3>
          <ul className="no-scrollbar flex gap-2 overflow-x-auto overflow-y-hidden pb-1">
            {scenes.map((v) => (
              <li key={v.id} className="w-24 shrink-0">
                <button type="button" onClick={() => setCurrent(v.url)} title={v.name} className={cn("block w-full overflow-hidden rounded-md border", current === v.url ? "border-foreground" : "border-border")}>
                  <video src={v.url + "#t=0.1"} preload="metadata" muted className="aspect-[9/14] w-full bg-black object-cover" />
                  <span className="block truncate px-1 py-0.5 text-[11px] text-muted-foreground">{v.name.split("/").pop()}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {images.length > 0 && (
        <section className="space-y-2">
          <h3 className="flex items-center gap-1.5 text-[13px] font-semibold"><Images className="h-4 w-4 text-muted-foreground" />{images.length}</h3>
          <ul className="no-scrollbar flex gap-2 overflow-x-auto overflow-y-hidden pb-1">
            {images.map((im) => (
              <li key={im.id} className="w-20 shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={im.url} alt={im.name} loading="lazy" title={im.name} className="aspect-[9/14] w-full rounded-md border border-border object-cover object-top" />
              </li>
            ))}
          </ul>
        </section>
      )}

      {scripts.length > 0 && (
        <section className="space-y-2">
          <div className="flex gap-1">
            {scripts.map((s, i) => (
              <button key={s.id} type="button" onClick={() => setScriptIdx(i)} title={s.name} className={cn("flex items-center gap-1 rounded-md border px-2 py-1 text-xs", i === scriptIdx ? "border-foreground bg-accent" : "border-border text-muted-foreground")}>
                <ScrollText className="h-3.5 w-3.5" />
                {s.name.replace(/\.md$/, "")}
              </button>
            ))}
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <Markdown>{text}</Markdown>
          </div>
        </section>
      )}
    </motion.div>
  );
}
