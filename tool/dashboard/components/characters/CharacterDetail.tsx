"use client";

import React, { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import type { Character } from "@/lib/repositories";
import { CORE_URL } from "@/lib/repositories";
import { Button } from "@/components/ui/Button";
import { Pencil, Copy, Trash2, Film, Plus, X } from "@/components/ui/icons";
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
  const [zoom, setZoom] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const imgInput = useRef<HTMLInputElement>(null);
  const voiceInput = useRef<HTMLInputElement>(null);

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: t("tabOverview") },
    { key: "images", label: `${t("tabImages")} (${c.referenceImages.length})` },
    { key: "voice", label: t("tabVoice") },
    { key: "clips", label: t("tabClips") },
  ];

  const avatar = c.referenceImages[0];

  return (
    <article className="rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          {avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={avatar} alt={c.name} className="h-16 w-16 shrink-0 rounded-md border border-border bg-muted/20 object-cover object-top" />
          ) : (
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-md border border-border bg-accent text-lg font-semibold text-muted-foreground">
              {c.name.replace("Bạn ", "").charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold leading-tight text-foreground">{c.name}</h2>
            <p className="text-[13px] text-muted-foreground">
              {c.role === "main" ? t("roleMain") : t("roleSupporting")} · <span className="tnum">{c.id}</span>
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Button size="sm" onClick={p.onAddToScript}>
            <Film className="h-3.5 w-3.5" />
            <span>{t("addToScript")}</span>
          </Button>
          <Button size="sm" variant="outline" onClick={p.onEdit}>
            <Pencil className="h-3.5 w-3.5" />
            <span>{t("edit")}</span>
          </Button>
          <Button size="sm" variant="outline" onClick={p.onDuplicate}>
            <Copy className="h-3.5 w-3.5" />
            <span>{t("duplicate")}</span>
          </Button>
          <Button size="sm" variant="outline" onClick={p.onDelete} className="text-semantic-danger">
            <Trash2 className="h-3.5 w-3.5" />
            <span>{t("delete")}</span>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div role="tablist" className="flex gap-1 overflow-x-auto border-b border-border px-3">
        {tabs.map((x) => (
          <button
            key={x.key}
            role="tab"
            aria-selected={tab === x.key}
            onClick={() => setTab(x.key)}
            className={cn(
              "-mb-px whitespace-nowrap border-b-2 px-3 py-2.5 text-[13px] font-medium transition-colors",
              tab === x.key ? "border-foreground text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {x.label}
          </button>
        ))}
      </div>

      <div className="space-y-5 p-4">
        {tab === "overview" && (
          <>
            <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Stat label={t("infoHeight")} value={t("cm", { value: c.heightCm })} />
              <Stat label={t("infoScale")} value={`${c.scaleRatio}x`} />
              <Stat label={t("infoVoice")} value={c.voiceId || "—"} />
              <Stat label={t("infoTempo")} value={`${c.defaultTempo ?? 1}x`} />
            </dl>
            <Block title={t("fDescription")}>
              <p className="text-[13px] leading-relaxed text-muted-foreground">{c.description || t("noDescription")}</p>
            </Block>
            <Block title={t("promptLock")}>
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
            </Block>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Block title={t("personality")}>
                <p className="text-[13px] text-foreground">{c.memory.personality || "—"}</p>
              </Block>
              <Block title={t("catchphrases")}>
                <Chips items={c.memory.catchphrases} />
              </Block>
              <Block title={t("habits")}>
                <Chips items={c.memory.habits} />
              </Block>
              <Block title={t("pastEvents")}>
                <Chips items={c.memory.pastEventsSummary} />
              </Block>
            </div>
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
              <Button size="sm" disabled={p.busy} onClick={() => imgInput.current?.click()}>
                <Plus className="h-3.5 w-3.5" />
                <span>{p.busy ? t("uploading") : t("uploadImages")}</span>
              </Button>
            </div>
            {c.referenceImages.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noImages")}</p>
            ) : (
              <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {c.referenceImages.map((url, i) => {
                  const name = baseName(url);
                  return (
                    <li key={url} className="group relative overflow-hidden rounded-md border border-border bg-muted/20">
                      <button type="button" className="block w-full" onClick={() => setZoom(url)} aria-label={name}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={url} alt={name} loading="lazy" className="aspect-square w-full object-cover object-top" />
                      </button>
                      {i === 0 && (
                        <span className="absolute left-1.5 top-1.5 rounded bg-primary px-1.5 py-0.5 text-[11px] font-medium text-primary-foreground">
                          {t("primary")}
                        </span>
                      )}
                      <div className="flex items-center justify-between gap-1 border-t border-border bg-card px-2 py-1">
                        <span className="truncate text-[12px] text-muted-foreground" title={name}>{name}</span>
                        <span className="flex shrink-0">
                          {i !== 0 && (
                            <button type="button" className="rounded px-1 text-[12px] text-foreground hover:bg-muted/60" onClick={() => p.onSetPrimary(name)}>
                              {t("setPrimary")}
                            </button>
                          )}
                          <button type="button" aria-label={t("removeImage")} title={t("removeImage")} className="rounded p-1 text-muted-foreground hover:bg-muted/60 hover:text-semantic-danger" onClick={() => p.onRemoveImage(name)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </span>
                      </div>
                    </li>
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
              <Button size="sm" className="mt-2" disabled={p.busy || !c.voiceId} onClick={() => voiceInput.current?.click()}>
                <Plus className="h-3.5 w-3.5" />
                <span>{p.busy ? t("uploading") : t("uploadVoice")}</span>
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

      {zoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setZoom(null)}>
          <button type="button" aria-label="Đóng" className="absolute right-4 top-4 rounded-full bg-card p-2 text-foreground" onClick={() => setZoom(null)}>
            <X className="h-4 w-4" />
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom} alt="" className="max-h-full max-w-full rounded-md object-contain" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </article>
  );
}
