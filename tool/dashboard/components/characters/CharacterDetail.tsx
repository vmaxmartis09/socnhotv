"use client";

import { enterOnce } from "@/lib/motion";
import React, { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import type { Character } from "@/lib/repositories";
import { CORE_URL } from "@/lib/repositories";
import { Button } from "@/components/ui/Button";
import { ChevronRight, Upload, Pencil, Copy, Trash2, Film, Plus, X, Ruler, Mic, Images, Clapperboard, Sparkles } from "@/components/ui/icons";
import { motion } from "framer-motion";
import { usePreview } from "@/lib/preview";
import { TiltedCard } from "./fx/TiltedCard";
import { cn } from "@/lib/utils";

type Tab = "overview" | "images" | "voice" | "clips";

interface Props {
  character: Character;
  busy: boolean;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onAddToScript: () => void;
  onSetPrimary: (filename: string) => void;
  onRemoveImage: (filename: string) => void;
  onUploadImages: (files: File[]) => void;
  onUploadVoice: (file: File) => void;
  onUseSample: (relativeUrl: string) => void;
  /** Thêm một mục vào bộ nhớ nhân vật (tính cách là chuỗi, các mục còn lại là danh sách). */
  onAddMemory: (field: "personality" | "catchphrases" | "habits" | "pastEventsSummary", value: string) => void;
}

const baseName = (url: string) => decodeURIComponent(url.split("/").pop() ?? url);

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold tnum text-foreground">{value}</dd>
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="text-[13px] font-semibold text-foreground">{title}</h3>
      {children}
    </section>
  );
}

function Chips({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-[13px] text-muted-foreground">—</p>;
  return (
    <ul className="flex flex-wrap gap-1.5">
      {items.map((x) => (
        <li key={x} className="rounded-full border border-border bg-muted/30 px-2.5 py-0.5 text-[13px] text-foreground">
          {x}
        </li>
      ))}
    </ul>
  );
}

export function CharacterDetail(p: Props) {
  const t = useTranslations("characters");
  const c = p.character;
  const [tab, setTab] = useState<Tab>("overview");
  const [heroIdx, setHeroIdx] = useState(0);
  const openImage = (index: number) =>
    usePreview.getState().open({
      kind: "image",
      title: c.name,
      items: c.referenceImages.map((u) => ({ url: u, name: baseName(u) })),
      index,
    });
  const stripRef = useRef<HTMLUListElement>(null);
  const [stripEdge, setStripEdge] = useState({ left: false, right: false });
  const measureStrip = React.useCallback(() => {
    const el = stripRef.current;
    if (!el) return;
    setStripEdge({ left: el.scrollLeft > 4, right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
  }, []);
  React.useEffect(() => {
    measureStrip();
    const el = stripRef.current;
    if (!el) return;
    const ro = new ResizeObserver(measureStrip);
    ro.observe(el);
    return () => ro.disconnect();
  }, [measureStrip, c.referenceImages.length]);
  const [copied, setCopied] = useState(false);
  const [adding, setAdding] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const imgInput = useRef<HTMLInputElement>(null);
  const voiceInput = useRef<HTMLInputElement>(null);

  const hasVoice = !!c.sampleAudioUrl || (c.voiceFiles ?? []).length > 0;
  const hasClips = (c.generatedClips ?? []).length > 0 || (c.appearances ?? []).length > 0;
  const tabs: { key: Tab; label: string; Icon: React.ComponentType<{ className?: string }>; empty?: boolean; soft?: boolean }[] = [
    { key: "overview", label: t("tabOverview"), Icon: Sparkles },
    { key: "images", label: `${t("tabImages")} (${c.referenceImages.length})`, Icon: Images, soft: c.referenceImages.length === 0 },
    { key: "voice", label: t("tabVoice"), Icon: Mic, soft: !hasVoice },
    { key: "clips", label: t("tabClips"), Icon: Clapperboard, empty: !hasClips },
  ];
  // Đoạn mô tả ngắn đặt phía trên dải ảnh: mô tả → tính cách → trích prompt lock
  const blurb = c.description || c.memory.personality || (c.promptLock ? c.promptLock.slice(0, 180) + (c.promptLock.length > 180 ? "…" : "") : "");
  const nImgs = c.referenceImages.length;

  const avatar = c.referenceImages[Math.min(heroIdx, Math.max(0, c.referenceImages.length - 1))];

  return (
    <article className="overflow-hidden rounded-2xl border border-border bg-card">
      {/* Trang cá nhân: ảnh chính lớn (nghiêng 3D), thông tin, dải ảnh, thao tác bằng biểu tượng */}
      <div className="relative overflow-hidden">
        {avatar && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatar} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full scale-125 object-cover object-top opacity-25 blur-3xl" />
        )}
        <div className="relative grid grid-cols-1 gap-4 p-3.5 sm:grid-cols-[240px_minmax(0,1fr)]">
          <div className="mx-auto h-[320px] w-[240px] sm:mx-0">
            {avatar ? (
              <div className="relative h-full w-full">
                <TiltedCard src={avatar} alt={c.name} caption={c.name} onClick={() => openImage(heroIdx)} />
                {nImgs > 1 && (
                  <>
                    <span className="pointer-events-none absolute right-3 top-3 z-10 rounded-full bg-black/55 px-2 py-0.5 text-[11px] text-white tnum">
                      {heroIdx + 1}/{nImgs}
                    </span>
                  </>
                )}
              </div>
            ) : (
              <div className="flex h-full w-full items-center justify-center rounded-[24px] border border-border bg-accent text-5xl font-semibold text-muted-foreground">
                {c.name.replace("Bạn ", "").charAt(0)}
              </div>
            )}
          </div>

          <div className="flex min-w-0 flex-col">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="truncate text-2xl font-semibold leading-tight tracking-tight text-foreground">{c.name}</h2>
                <p className="text-[13px] text-muted-foreground">
                  {c.role === "main" ? t("roleMain") : t("roleSupporting")} · <span className="tnum">@{c.id}</span>
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                {[
                  { label: t("addToScript"), Icon: Film, onClick: p.onAddToScript, primary: true },
                  { label: t("edit"), Icon: Pencil, onClick: p.onEdit },
                  { label: t("duplicate"), Icon: Copy, onClick: p.onDuplicate },
                  { label: t("delete"), Icon: Trash2, onClick: p.onDelete, danger: true },
                ].map(({ label, Icon, onClick, primary, danger }) => (
                  <motion.button
                    key={label}
                    type="button"
                    title={label}
                    aria-label={label}
                    onClick={onClick}
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.88 }}
                    className={cn(
                      "flex h-9 w-9 items-center justify-center rounded-full border transition-colors",
                      primary
                        ? "border-transparent bg-primary text-primary-foreground"
                        : danger
                        ? "border-border bg-card text-semantic-danger hover:bg-accent"
                        : "border-border bg-card text-foreground hover:bg-accent"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </motion.button>
                ))}
              </div>
            </div>

            <ul className="mt-2 flex flex-wrap gap-1.5 text-[13px]">
              {[
                { Icon: Ruler, text: `${c.heightCm} cm · ${c.scaleRatio}x`, tip: t("infoHeight") },
                { Icon: Mic, text: `${c.voiceId || "—"} · ${c.defaultTempo ?? 1}x`, tip: t("infoVoice") },
                { Icon: Images, text: String(c.referenceImages.length), tip: t("tabImages") },
                { Icon: Clapperboard, text: String((c.generatedClips ?? []).length), tip: t("tabClips") },
              ].map(({ Icon, text, tip }) => (
                <li key={tip} title={tip} className="flex items-center gap-1.5 rounded-full border border-border bg-card/70 px-2.5 py-1 text-foreground tnum">
                  <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  {text}
                </li>
              ))}
            </ul>

            {blurb && <p className="mt-2 line-clamp-3 text-[13px] leading-relaxed text-muted-foreground">{blurb}</p>}

            {/* Dải ảnh lớn: bấm để xem toàn màn hình */}
            {c.referenceImages.length > 1 && (
              <div className="relative mt-auto min-w-0">
              <ul
                ref={stripRef}
                onScroll={measureStrip}
                onWheel={(e) => {
                  if (stripRef.current && Math.abs(e.deltaY) > Math.abs(e.deltaX)) stripRef.current.scrollLeft += e.deltaY;
                }}
                className="no-scrollbar flex gap-2 overflow-x-auto overflow-y-hidden pt-2.5"
              >
                {c.referenceImages.map((u, i) => (
                  <motion.li key={u} initial={enterOnce(`thumb:${u}`, { opacity: 0, y: 8 })} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i, 10) * 0.04 }} className="shrink-0">
                    <button
                      type="button"
                      onClick={() => setHeroIdx(i)}
                      onDoubleClick={() => openImage(i)}
                      className={cn("block overflow-hidden rounded-2xl border-2 transition-all hover:-translate-y-0.5", i === heroIdx ? "border-foreground" : "border-border")}
                      title={`${baseName(u)} — click để đặt làm ảnh đại diện, nhấn đúp để xem lớn`}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={u} alt="" loading="lazy" className="h-28 w-20 object-cover object-top" />
                    </button>
                  </motion.li>
                ))}
              </ul>
              {(["left", "right"] as const).map((side) =>
                stripEdge[side] ? (
                  <button
                    key={side}
                    type="button"
                    title={side === "left" ? "Ảnh trước" : "Ảnh sau"}
                    aria-label={side === "left" ? "Cuộn ảnh trước" : "Cuộn ảnh sau"}
                    onClick={() => stripRef.current?.scrollBy({ left: (side === "left" ? -1 : 1) * 240, behavior: "smooth" })}
                    className={cn("absolute top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card/95 text-foreground shadow-sm backdrop-blur transition-transform active:scale-90", side === "left" ? "left-1" : "right-1")}
                  >
                    <ChevronRight className={cn("h-4 w-4", side === "left" && "rotate-180")} />
                  </button>
                ) : null
              )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab: chỉ biểu tượng, tên hiện khi rê chuột */}
      <div role="tablist" className="no-scrollbar flex justify-start gap-1 overflow-x-auto overflow-y-hidden border-y border-border px-3">
        {tabs.map((x) => (
          <button
            key={x.key}
            role="tab"
            aria-selected={tab === x.key}
            title={x.empty ? `${x.label} — trống` : x.soft ? `${x.label} — trống, bấm để thêm` : x.label}
            aria-label={x.label}
            aria-disabled={x.empty}
            disabled={x.empty}
            onClick={() => {
              usePreview.getState().close();
              setTab(x.key);
            }}
            className={cn(
              "relative flex h-10 w-12 items-center justify-center transition-colors",
              x.empty
                ? "cursor-not-allowed opacity-30"
                : x.soft && tab !== x.key ? "text-muted-foreground opacity-50 hover:opacity-100" : tab === x.key ? "text-foreground" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <x.Icon className="h-4 w-4" />
            {tab === x.key && <motion.span layoutId={`char-tab-${c.id}`} className="absolute inset-x-2 -bottom-px h-0.5 rounded bg-foreground" />}
          </button>
        ))}
      </div>

      <div className="space-y-3 p-3">
        {tab === "overview" && (
          <>
            <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Stat label={t("infoHeight")} value={t("cm", { value: c.heightCm })} />
              <Stat label={t("infoScale")} value={`${c.scaleRatio}x`} />
              <Stat label={t("infoVoice")} value={c.voiceId || "—"} />
              <Stat label={t("infoTempo")} value={`${c.defaultTempo ?? 1}x`} />
            </dl>
            {c.promptLock && (<Block title={t("promptLock")}>
              <div className="relative">
                <p className="rounded-md border border-border bg-muted/20 p-3 pr-20 text-[13px] leading-relaxed text-muted-foreground">
                  {c.promptLock || "—"}
                </p>
                <Button
                  size="sm"
                  variant="ghost"
                  className="absolute right-2 top-2"
                  onClick={() => {
                    navigator.clipboard?.writeText(c.promptLock).then(() => {
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    });
                  }}
                >
                  {copied ? t("copied") : t("copyPrompt")}
                </Button>
              </div>
            </Block>)}
            {(() => {
              const m = c.memory;
              const blocks: { key: string; title: string; filled: boolean; node: React.ReactNode }[] = [
                { key: "personality", title: t("personality"), filled: !!m.personality, node: <p className="text-[13px] text-foreground">{m.personality}</p> },
                { key: "catch", title: t("catchphrases"), filled: m.catchphrases.length > 0, node: <Chips items={m.catchphrases} /> },
                { key: "habits", title: t("habits"), filled: m.habits.length > 0, node: <Chips items={m.habits} /> },
                { key: "events", title: t("pastEvents"), filled: m.pastEventsSummary.length > 0, node: <Chips items={m.pastEventsSummary} /> },
              ];
              const filled = blocks.filter((x) => x.filled);
              const empty = blocks.filter((x) => !x.filled);
              return (
                <>
                  {filled.length > 0 && (
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                      {filled.map((x) => (
                        <Block key={x.key} title={x.title}>{x.node}</Block>
                      ))}
                    </div>
                  )}
                  {/* Mục trống: dòng nét đứt với nút + cho từng mục, bấm để nhập ngay tại chỗ */}
                  {empty.length > 0 && (
                    <div className="space-y-2 rounded-xl border border-dashed border-border p-2">
                      <div className="flex flex-wrap gap-1.5">
                        {empty.map((x) => (
                          <button
                            key={x.key}
                            type="button"
                            title={`Thêm ${x.title.toLowerCase()}`}
                            onClick={() => { setAdding(adding === x.key ? null : x.key); setDraft(""); }}
                            className={cn("inline-flex h-7 items-center gap-1 rounded-full border px-2.5 text-xs transition-colors active:scale-95", adding === x.key ? "border-foreground text-foreground" : "border-border text-muted-foreground hover:border-foreground hover:text-foreground")}
                          >
                            <Plus className="h-3 w-3" />{x.title}
                          </button>
                        ))}
                      </div>
                      {adding && empty.some((x) => x.key === adding) && (
                        <form
                          className="flex items-center gap-1.5"
                          onSubmit={(e) => {
                            e.preventDefault();
                            const v = draft.trim();
                            if (!v) return;
                            const field = ({ personality: "personality", catch: "catchphrases", habits: "habits", events: "pastEventsSummary" } as const)[adding as "personality" | "catch" | "habits" | "events"];
                            p.onAddMemory(field, v);
                            setAdding(null);
                            setDraft("");
                          }}
                        >
                          <input
                            autoFocus
                            value={draft}
                            onChange={(e) => setDraft(e.target.value)}
                            onKeyDown={(e) => e.key === "Escape" && setAdding(null)}
                            placeholder={`${empty.find((x) => x.key === adding)?.title} — nhập rồi Enter`}
                            className="h-8 min-w-0 flex-1 rounded-lg border border-border bg-card px-2.5 text-[13px]"
                          />
                          <button type="submit" title="Lưu" aria-label="Lưu" disabled={!draft.trim()} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground active:scale-90 disabled:opacity-40">
                            <Plus className="h-4 w-4" />
                          </button>
                        </form>
                      )}
                    </div>
                  )}
                </>
              );
            })()}
          </>
        )}

        {tab === "images" && (
          <>
            <div className="flex items-center justify-between">
              <p className="text-[13px] text-muted-foreground">{t("imageCount", { count: c.referenceImages.length })}</p>
              <input
                ref={imgInput}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                hidden
                onChange={(e) => {
                  const files = Array.from(e.target.files ?? []);
                  e.target.value = "";
                  if (files.length) p.onUploadImages(files);
                }}
              />
              <Button size="icon" title={t("uploadImages")} aria-label={t("uploadImages")} disabled={p.busy} onClick={() => imgInput.current?.click()}>
                <Upload className="h-3.5 w-3.5" />
                <span className="sr-only">{p.busy ? t("uploading") : t("uploadImages")}</span>
              </Button>
            </div>
            {c.referenceImages.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noImages")}</p>
            ) : (
              <ul className="columns-2 gap-3 sm:columns-3 [&>li]:mb-3">
                {c.referenceImages.map((url, i) => {
                  const name = baseName(url);
                  return (
                    <motion.li
                      key={url}
                      initial={enterOnce(`img:${url}`, { opacity: 0, y: 12 })}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: Math.min(i, 10) * 0.03 }}
                      className="group relative break-inside-avoid overflow-hidden rounded-2xl border border-border bg-muted/20"
                    >
                      <button type="button" className="block w-full" onClick={() => openImage(i)} aria-label={name} title={name}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={url} alt={name} loading="lazy" className="w-full object-cover transition-transform duration-300 group-hover:scale-[1.04]" />
                      </button>
                      {i === 0 && (
                        <span className="absolute left-2 top-2 rounded-full bg-primary px-2 py-0.5 text-[11px] font-medium text-primary-foreground">{t("primary")}</span>
                      )}
                      <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        {i !== 0 && (
                          <button type="button" title={t("setPrimary")} aria-label={t("setPrimary")} className="flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-foreground backdrop-blur hover:bg-card active:scale-90" onClick={() => p.onSetPrimary(name)}>
                            <Sparkles className="h-3.5 w-3.5" />
                          </button>
                        )}
                        <button type="button" title={t("removeImage")} aria-label={t("removeImage")} className="flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-semantic-danger backdrop-blur hover:bg-card active:scale-90" onClick={() => p.onRemoveImage(name)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </motion.li>
                  );
                })}
              </ul>
            )}
          </>
        )}

        {tab === "voice" && (
          <>
            <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <Stat label={t("infoVoice")} value={c.voiceId || "—"} />
              <Stat label={t("infoTempo")} value={`${c.defaultTempo ?? 1}x`} />
            </dl>
            <Block title={t("voiceSample")}>
              {c.sampleAudioUrl ? (
                <audio controls preload="none" src={c.sampleAudioUrl} className="w-full" />
              ) : (
                <p className="text-[13px] text-muted-foreground">{t("noVoice")}</p>
              )}
            </Block>
            <Block title={t("voiceFiles")}>
              <input
                ref={voiceInput}
                type="file"
                accept="audio/mpeg,audio/wav,.mp3,.wav"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  e.target.value = "";
                  if (f) p.onUploadVoice(f);
                }}
              />
              <ul className="space-y-2">
                {(c.voiceFiles ?? []).map((f) => {
                  const rel = f.url.replace(CORE_URL, "");
                  const active = c.sampleAudioUrl?.replace(CORE_URL, "") === rel;
                  return (
                    <li key={f.name} className="rounded-md border border-border p-2.5">
                      <div className="mb-1.5 flex items-center justify-between gap-2 text-[13px]">
                        <span className="truncate font-medium text-foreground">{f.name} <span className="font-normal text-muted-foreground tnum">· {f.sizeKb} KB</span></span>
                        {active ? (
                          <span className="shrink-0 text-xs text-brand">{t("usingSample")}</span>
                        ) : (
                          <Button size="sm" variant="outline" onClick={() => p.onUseSample(rel)}>{t("useSample")}</Button>
                        )}
                      </div>
                      <audio controls preload="none" src={f.url} className="h-8 w-full" />
                    </li>
                  );
                })}
              </ul>
              <Button size="icon" className="mt-2" title={t("uploadVoice")} aria-label={t("uploadVoice")} disabled={p.busy || !c.voiceId} onClick={() => voiceInput.current?.click()}>
                <Upload className="h-3.5 w-3.5" />
                <span className="sr-only">{p.busy ? t("uploading") : t("uploadVoice")}</span>
              </Button>
            </Block>
          </>
        )}

        {tab === "clips" && (
          <>
            <Block title={t("tabClips")}>
              {(c.generatedClips ?? []).length === 0 ? (
                <p className="text-[13px] text-muted-foreground">{t("noClips")}</p>
              ) : (
                <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {(c.generatedClips ?? []).map((clip) => (
                    <li key={clip.id} className="overflow-hidden rounded-md border border-border">
                      <video controls preload="none" poster={clip.thumbnailUrl} src={clip.url} className="aspect-video w-full bg-black object-contain" />
                      <div className="p-2.5 text-[13px]">
                        <p className="font-medium text-foreground">{clip.sceneTitle}</p>
                        <p className="text-muted-foreground">{clip.episodeTitle} · <span className="tnum">{clip.durationSec}s</span> · {clip.model}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Block>
            <Block title={t("appearances")}>
              {(c.appearances ?? []).length === 0 ? (
                <p className="text-[13px] text-muted-foreground">{t("noAppearances")}</p>
              ) : (
                <ul className="space-y-2">
                  {(c.appearances ?? []).map((a) => (
                    <li key={a.episodeId} className="rounded-md border border-border p-2.5">
                      <p className="text-[13px] font-medium text-foreground">{a.episodeTitle}</p>
                      <div className="mt-1.5"><Chips items={a.scenes} /></div>
                    </li>
                  ))}
                </ul>
              )}
            </Block>
          </>
        )}
      </div>

    </article>
  );
}
