"use client";

import React from "react";
import type { StudioNodeData } from "@/store/slices/canvasSlice";
import type { Character } from "@/lib/repositories";
import { Film, Download, ScrollText, ShieldCheck, Volume2, Video, Images } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

interface Props {
  nodeType: string;
  nodeId: string;
  data: StudioNodeData;
  character?: Character;
  /** Cổng vào đã nối (tên cổng) — dùng cho thân "Dựng" để vẽ các track */
  connectedInputs: string[];
  /** Thu gọn vừa phải: vẫn giữ ảnh/nội dung chính, bỏ phần chi tiết phụ */
  compact?: boolean;
}

const Chip = ({ children, title }: { children: React.ReactNode; title?: string }) => (
  <span title={title} className="rounded-full border border-border bg-muted/30 px-2 py-0.5 text-[11px] text-muted-foreground tnum">
    {children}
  </span>
);

/** Sóng âm giả lập tất định từ id node (chỉ để nhận diện nhanh, không phải dữ liệu thật). */
function Wave({ seed, active }: { seed: string; active: boolean }) {
  let h = 0;
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const bars = Array.from({ length: 36 }, (_, i) => {
    h = (h * 1103515245 + 12345) >>> 0;
    return 20 + ((h >>> 16) % 80);
  });
  return (
    <div className="flex h-8 items-center gap-[2px]" aria-hidden="true">
      {bars.map((b, i) => (
        <span key={i} style={{ height: `${b}%` }} className={cn("w-[3px] rounded-full", active ? "bg-brand/70" : "bg-border")} />
      ))}
    </div>
  );
}

function ImagePreview({ url, alt, compact }: { url?: string; alt: string; compact?: boolean }) {
  if (!url) return <Empty icon={<Images className="h-6 w-6" />} text="Ảnh sẽ hiện ở đây" tall />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={alt} loading="lazy" className={cn("w-full rounded-lg border border-border object-cover object-top", compact ? "max-h-32" : "max-h-72")} />;
}

function Empty({ icon, text, tall }: { icon: React.ReactNode; text?: string; tall?: boolean }) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-1 rounded-md border border-dashed border-border text-muted-foreground", tall ? "h-40" : "h-20")}>
      {icon}
      {text && <span className="text-[11px]">{text}</span>}
    </div>
  );
}

/** Thẻ nhân vật gọn: 1 ảnh lớn + tên + chip thông số. Chi tiết xem ở panel bên phải. */
function CharacterHero({ c, compact }: { c: Character; compact?: boolean }) {
  const gallery = c.referenceImages.slice(1, 5);
  return (
    <div className="space-y-1.5">
      {c.referenceImages[0] ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={c.referenceImages[0]} alt={c.name} className={cn("w-full rounded-lg border border-border bg-muted/20 object-cover object-top", compact ? "h-32" : "h-56")} />
      ) : (
        <Empty icon={<ShieldCheck className="h-6 w-6" />} text={c.name} tall />
      )}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-sm font-semibold text-foreground">{c.name}</span>
        <Chip title="Chiều cao">{c.heightCm} cm</Chip>
        <Chip title="Giọng">{c.voiceId || "—"}</Chip>
      </div>
      {!compact && (
        <>
          <p className="text-xs text-muted-foreground">
            {c.role === "main" ? "Nhân vật chính" : "Nhân vật phụ"} · tỉ lệ {c.scaleRatio}x · giọng {c.defaultTempo ?? 1}x
          </p>
          {gallery.length > 0 && (
            <div className="flex gap-1 overflow-hidden">
              {gallery.map((u) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={u} src={u} alt="" loading="lazy" className="h-10 w-10 rounded border border-border object-cover object-top" />
              ))}
              {c.referenceImages.length > 5 && (
                <span className="flex h-10 w-10 items-center justify-center rounded border border-border text-xs text-muted-foreground tnum">+{c.referenceImages.length - 5}</span>
              )}
            </div>
          )}
          {c.memory.personality && (
            <p className="line-clamp-2 text-xs text-muted-foreground"><span className="font-medium text-foreground">Tính cách: </span>{c.memory.personality}</p>
          )}
          {c.memory.catchphrases.length > 0 && (
            <p className="line-clamp-1 text-xs italic text-muted-foreground">“{c.memory.catchphrases[0]}”</p>
          )}
          {c.sampleAudioUrl && <audio controls preload="none" src={c.sampleAudioUrl} className="nodrag nowheel h-7 w-full" />}
        </>
      )}
    </div>
  );
}

/** Thân card riêng cho từng loại node: nhìn là hiểu node đó làm gì và đã ra gì. */
export function NodeBody({ nodeType, nodeId, data, character, connectedInputs, compact }: Props) {
  const p = data.params || {};
  const url = data.previewUrl;
  const done = data.status === "succeeded";
  const lines = (data.summaryText || "").split("\n").map((l) => l.trim()).filter(Boolean);

  switch (nodeType) {
    case "text": {
      const content = typeof p.content === "string" ? p.content.trim() : "";
      const words = content ? content.split(/\s+/).length : 0;
      return (
        <div className="space-y-1.5">
          <p className="line-clamp-5 rounded-md border border-border bg-muted/20 p-2 text-xs leading-relaxed text-foreground">{content || "—"}</p>
          <div className="flex gap-1.5"><Chip title="Số từ">{words} từ</Chip></div>
        </div>
      );
    }
    case "image":
    case "character_image":
    case "scene":
      return <ImagePreview url={url ?? p.uri ?? p.url} alt={nodeType} compact={compact} />;

    case "transition":
      return (
        <div className="flex items-center justify-center gap-2 rounded-md border border-dashed border-border py-3 text-xs text-muted-foreground">
          <span className="h-6 w-8 rounded bg-muted" />
          <span className="font-mono text-foreground">{String(p.style || "fade")}</span>
          <span className="h-6 w-8 rounded bg-muted" />
        </div>
      );

    case "character":
      return character ? <CharacterHero c={character} compact={compact} /> : <Empty icon={<ShieldCheck className="h-5 w-5" />} text={String(p.characterId || "—")} />;

    case "script": {
      const count = p.targetSceneCount ?? lines.length;
      return (
        <div className="space-y-1.5">
          <div className="flex flex-wrap gap-1.5">
            <Chip title="Số cảnh">{count} cảnh</Chip>
            {p.durationSec ? <Chip title="Thời lượng">{p.durationSec}s</Chip> : null}
          </div>
          {lines.length > 0 ? (
            <ol className="space-y-0.5 rounded-md border border-border bg-muted/20 p-2 text-xs">
              {lines.slice(0, 6).map((l, i) => (
                <li key={i} className="flex gap-1.5">
                  <span className="w-4 shrink-0 text-right text-muted-foreground tnum">{i + 1}</span>
                  <span className="truncate text-foreground">{l.replace(/^\d+[.)]\s*/, "")}</span>
                </li>
              ))}
            </ol>
          ) : (
            <Empty icon={<ScrollText className="h-5 w-5" />} />
          )}
        </div>
      );
    }

    case "quality_check": {
      const threshold = Number(p.thresholdScore ?? 0.85);
      const m = (data.summaryText || "").match(/\d*\.?\d+/);
      const score = done && m ? Math.min(1, Number(m[0])) : null;
      const pass = score !== null && score >= threshold;
      return (
        <div className="space-y-1.5">
          <div className="relative h-2.5 overflow-hidden rounded-full bg-muted">
            {score !== null && <div style={{ width: `${score * 100}%` }} className={cn("h-full rounded-full transition-all", pass ? "bg-semantic-success" : "bg-semantic-danger")} />}
            <span style={{ left: `${threshold * 100}%` }} className="absolute inset-y-0 w-0.5 bg-foreground" title={`Ngưỡng ${threshold}`} />
          </div>
          <div className="flex items-center justify-between text-xs tnum">
            <span className="text-muted-foreground">≥ {threshold}</span>
            <span className={cn("font-semibold", score === null ? "text-muted-foreground" : pass ? "text-semantic-success" : "text-semantic-danger")}>
              {score === null ? "—" : `${score.toFixed(2)} ${pass ? "✓" : "✕"}`}
            </span>
          </div>
        </div>
      );
    }

    case "image_gen":
    case "image_edit":
      return (
        <div className="space-y-1.5">
          <ImagePreview url={url} alt={nodeType} compact={compact} />
        </div>
      );

    case "video_gen":
      return (
        <div className="space-y-1.5">
          {url && data.previewType === "video" ? (
            <video src={url} controls preload="metadata" className="nodrag max-h-48 w-full rounded-md border border-border bg-black object-contain" />
          ) : (
            <Empty icon={<Video className="h-6 w-6" />} text="Video sẽ hiện ở đây" tall />
          )}
        </div>
      );

    case "voice_tts":
      return (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 rounded-md border border-border bg-muted/20 px-2 py-1.5">
            <Volume2 className="h-4 w-4 shrink-0 text-muted-foreground" />
            <Wave seed={nodeId} active={done} />
          </div>
          {url && data.previewType === "audio" && <audio src={url} controls preload="metadata" className="nodrag h-7 w-full" />}
        </div>
      );

    case "captions":
      return lines.length > 0 ? (
        <ul className="space-y-0.5 rounded-md border border-border bg-muted/20 p-2 text-xs">
          {lines.slice(0, 4).map((l, i) => <li key={i} className="truncate">{l}</li>)}
        </ul>
      ) : (
        <Empty icon={<ScrollText className="h-5 w-5" />} />
      );

    case "hyperframes_render": {
      const tracks: [string, string][] = [
        ["video", "bg-[#b4531a]"],
        ["audio", "bg-[#a86f0c]"],
        ["captions", "bg-[#737373]"],
        ["bgm", "bg-[#a86f0c]/50"],
      ];
      return (
        <div className="space-y-1.5">
          <div className="space-y-1 rounded-md border border-border bg-muted/20 p-2" aria-label="timeline">
            {tracks.map(([name, color]) => {
              const on = connectedInputs.includes(name);
              return (
                <div key={name} className="flex items-center gap-2" title={name}>
                  <span className="w-12 shrink-0 text-[10px] text-muted-foreground">{name}</span>
                  <span className={cn("h-2 flex-1 rounded-full", on ? color : "bg-border/60")} />
                </div>
              );
            })}
          </div>
          {url && data.previewType === "video" && <video src={url} controls preload="metadata" className="nodrag max-h-48 w-full rounded-md bg-black object-contain" />}
        </div>
      );
    }

    case "export":
      return (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 rounded-md border border-border bg-muted/20 p-2">
            <Film className="h-4 w-4 shrink-0 text-brand" />
            <span className="min-w-0 flex-1 truncate font-mono text-xs">{String(p.outputFileName || "output.mp4")}</span>
            {url && (
              <a href={url} download title="Tải xuống" aria-label="Tải xuống" className="nodrag flex h-6 w-6 items-center justify-center rounded border border-border hover:bg-accent">
                <Download className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
          {url && data.previewType === "video" && <video src={url} controls preload="metadata" className="nodrag max-h-48 w-full rounded-md bg-black object-contain" />}
        </div>
      );

    default:
      if (url && data.previewType === "image") return <ImagePreview url={url} alt={nodeType} compact={compact} />;
      if (url && data.previewType === "video") return <video src={url} controls preload="metadata" className="nodrag max-h-48 w-full rounded-md bg-black" />;
      if (url && data.previewType === "audio") return <audio src={url} controls preload="metadata" className="nodrag h-7 w-full" />;
      return null;
  }
}
