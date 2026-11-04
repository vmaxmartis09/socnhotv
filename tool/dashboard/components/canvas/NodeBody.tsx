"use client";

import React from "react";
import type { StudioNodeData } from "@/store/slices/canvasSlice";
import type { Character } from "@/lib/repositories";
import { useStudioStore } from "@/store";
import {
  Film,
  Download,
  ScrollText,
  ShieldCheck,
  Volume2,
  Video,
  Images,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import {
  NodeTextInput,
  NodeImageInput,
  NodeScriptInput,
  NodeVoiceInput,
  NodeImageGenInput,
  NodeExportInput,
  NodeCharacterSelect,
  NodeCaptionsInput,
} from "./NodeInputs";

interface Props {
  nodeType: string;
  nodeId: string;
  data: StudioNodeData;
  character?: Character;
  /** Cổng vào đã nối (tên cổng) */
  connectedInputs: string[];
  /** Thu gọn vừa phải */
  compact?: boolean;
}

const Chip = ({
  children,
  title,
}: {
  children: React.ReactNode;
  title?: string;
}) => (
  <span
    title={title}
    className="rounded-full border border-border bg-muted/30 px-2 py-0.5 text-[11px] text-muted-foreground tnum"
  >
    {children}
  </span>
);

function Empty({
  icon,
  text,
  tall,
}: {
  icon: React.ReactNode;
  text?: string;
  tall?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-1 rounded-md border border-dashed border-border text-muted-foreground",
        tall ? "h-36" : "h-20"
      )}
    >
      {icon}
      {text && <span className="text-[11px]">{text}</span>}
    </div>
  );
}

function ImagePreview({
  url,
  alt,
  compact,
}: {
  url?: string;
  alt: string;
  compact?: boolean;
}) {
  if (!url)
    return (
      <Empty
        icon={<Images className="h-6 w-6" />}
        text="Ảnh sẽ hiện ở đây"
        tall
      />
    );
  // eslint-disable-next-line @next/next/no-img-element
  return (
    <img
      src={url}
      alt={alt}
      loading="lazy"
      className={cn(
        "w-full rounded-lg border border-border object-cover object-top",
        compact ? "max-h-32" : "max-h-64"
      )}
    />
  );
}

/** Thẻ nhân vật gọn: 1 ảnh lớn + tên + chip thông số */
function CharacterHero({ c, compact }: { c: Character; compact?: boolean }) {
  const gallery = c.referenceImages.slice(1, 5);
  return (
    <div className="space-y-1.5 pt-1">
      {c.referenceImages[0] ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={c.referenceImages[0]}
          alt={c.name}
          className={cn(
            "w-full rounded-lg border border-border bg-muted/20 object-cover object-top",
            compact ? "h-28" : "h-48"
          )}
        />
      ) : (
        <Empty icon={<ShieldCheck className="h-6 w-6" />} text={c.name} tall />
      )}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-sm font-semibold text-foreground">
          {c.name}
        </span>
        <Chip title="Chiều cao">{c.heightCm} cm</Chip>
        <Chip title="Giọng">{c.voiceId || "—"}</Chip>
      </div>
      {!compact && (
        <>
          <p className="text-xs text-muted-foreground">
            {c.role === "main" ? "Nhân vật chính" : "Nhân vật phụ"} · tỉ lệ{" "}
            {c.scaleRatio}x
          </p>
          {gallery.length > 0 && (
            <div className="flex gap-1 overflow-hidden">
              {gallery.map((u) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={u}
                  src={u}
                  alt=""
                  loading="lazy"
                  className="h-10 w-10 rounded border border-border object-cover object-top"
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/** Thân card cho từng loại node: cho phép nhập liệu trực tiếp ngay trên card. */
export function NodeBody({
  nodeType,
  nodeId,
  data,
  character,
  connectedInputs,
  compact,
}: Props) {
  const { updateNodeParams } = useStudioStore();
  const p = data.params || {};
  const url = data.previewUrl;
  const done = data.status === "succeeded";
  const lines = (data.summaryText || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  switch (nodeType) {
    case "text":
      return (
        <NodeTextInput
          nodeId={nodeId}
          content={typeof p.content === "string" ? p.content : ""}
          connected={connectedInputs.includes("text")}
        />
      );

    case "image":
    case "character_image":
    case "scene":
      return (
        <NodeImageInput
          nodeId={nodeId}
          uri={p.uri}
          name={p.name}
          nodeType={nodeType}
          previewUrl={url}
          compact={compact}
        />
      );

    case "script":
      return (
        <NodeScriptInput
          nodeId={nodeId}
          mode={p.mode}
          rawScript={p.rawScript}
          ideaText={p.text || p.content}
          targetSceneCount={p.targetSceneCount}
          targetDurationSec={p.targetDurationSec}
          connectedText={connectedInputs.includes("text")}
        />
      );

    case "voice_tts":
      return (
        <div className="space-y-2">
          <NodeVoiceInput
            nodeId={nodeId}
            text={p.text}
            voiceId={p.voiceId}
            tempo={p.tempo}
            connectedText={connectedInputs.includes("text")}
          />
          {url && data.previewType === "audio" && (
            <div className="pt-1">
              <audio
                src={url}
                controls
                preload="metadata"
                className="nodrag h-7 w-full"
              />
            </div>
          )}
        </div>
      );

    case "image_gen":
    case "image_edit":
      return (
        <div className="space-y-2">
          {url && (
            <div className="space-y-1">
              <ImagePreview url={url} alt={nodeType} compact={compact} />
            </div>
          )}
          <NodeImageGenInput
            nodeId={nodeId}
            prompt={p.prompt}
            referenceImages={p.referenceImages}
            aspectRatio={p.aspectRatio}
            model={p.model}
            connectedPrompt={connectedInputs.includes("prompt")}
          />
        </div>
      );

    case "video_gen":
      return (
        <div className="space-y-2">
          {url && data.previewType === "video" ? (
            <video
              src={url}
              controls
              preload="metadata"
              className="nodrag max-h-48 w-full rounded-md border border-border bg-black object-contain"
            />
          ) : (
            <Empty
              icon={<Video className="h-6 w-6" />}
              text="Video sẽ hiện ở đây"
              tall
            />
          )}
          {!connectedInputs.includes("prompt") && (
            <textarea
              rows={2}
              value={p.prompt || ""}
              onChange={(e) =>
                updateNodeParams(nodeId, { prompt: e.target.value })
              }
              placeholder="Prompt chuyển động video..."
              className="nodrag nowheel w-full rounded border border-border bg-card p-1.5 text-xs text-foreground placeholder:text-muted-foreground/60"
            />
          )}
        </div>
      );

    case "character":
      return (
        <div className="space-y-2">
          <NodeCharacterSelect
            nodeId={nodeId}
            characterId={p.characterId || "soc_nho"}
          />
          {character && <CharacterHero c={character} compact={compact} />}
        </div>
      );

    case "captions":
      return (
        <div className="space-y-2">
          <NodeCaptionsInput
            nodeId={nodeId}
            style={p.style}
            language={p.language}
          />
          {lines.length > 0 && (
            <ul className="space-y-0.5 rounded-md border border-border bg-muted/20 p-2 text-xs">
              {lines.slice(0, 4).map((l, i) => (
                <li key={i} className="truncate text-muted-foreground">
                  {l}
                </li>
              ))}
            </ul>
          )}
        </div>
      );

    case "transition":
      return (
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground w-16">Hiệu ứng:</span>
            <select
              value={p.style || "fade"}
              onChange={(e) =>
                updateNodeParams(nodeId, { style: e.target.value })
              }
              className="nodrag h-7 flex-1 rounded border border-border bg-card px-2 text-xs text-foreground"
            >
              <option value="fade">Fade (Mờ dần)</option>
              <option value="dissolve">Dissolve (Hòa tan)</option>
              <option value="wipe_left">Wipe (Gạt ngang)</option>
              <option value="slide_up">Slide (Trượt lên)</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground w-16">Thời lượng:</span>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="3"
              value={p.durationSec ?? 0.5}
              onChange={(e) =>
                updateNodeParams(nodeId, {
                  durationSec: Number(e.target.value) || 0.5,
                })
              }
              className="nodrag h-7 w-20 rounded border border-border bg-card px-2 text-xs tnum text-foreground"
            />
            <span className="text-muted-foreground">giây</span>
          </div>
        </div>
      );

    case "hyperframes_render": {
      const tracks: [string, string][] = [
        ["video", "bg-[#b4531a]"],
        ["audio", "bg-[#a86f0c]"],
        ["captions", "bg-[#737373]"],
        ["bgm", "bg-[#a86f0c]/50"],
      ];
      return (
        <div className="space-y-2">
          <div
            className="space-y-1 rounded-md border border-border bg-muted/20 p-2"
            aria-label="timeline"
          >
            {tracks.map(([name, color]) => {
              const on = connectedInputs.includes(name);
              return (
                <div
                  key={name}
                  className="flex items-center gap-2"
                  title={name}
                >
                  <span className="w-12 shrink-0 text-[10px] text-muted-foreground">
                    {name}
                  </span>
                  <span
                    className={cn(
                      "h-2 flex-1 rounded-full",
                      on ? color : "bg-border/60"
                    )}
                  />
                </div>
              );
            })}
          </div>
          {url && data.previewType === "video" && (
            <video
              src={url}
              controls
              preload="metadata"
              className="nodrag max-h-48 w-full rounded-md bg-black object-contain"
            />
          )}
        </div>
      );
    }

    case "export":
      return (
        <div className="space-y-2">
          <NodeExportInput
            nodeId={nodeId}
            outputFileName={p.outputFileName}
            platforms={p.platforms}
            previewUrl={url}
          />
          {url && data.previewType === "video" && (
            <video
              src={url}
              controls
              preload="metadata"
              className="nodrag max-h-48 w-full rounded-md bg-black object-contain"
            />
          )}
        </div>
      );

    default:
      if (url && data.previewType === "image")
        return <ImagePreview url={url} alt={nodeType} compact={compact} />;
      if (url && data.previewType === "video")
        return (
          <video
            src={url}
            controls
            preload="metadata"
            className="nodrag max-h-48 w-full rounded-md bg-black"
          />
        );
      if (url && data.previewType === "audio")
        return (
          <audio
            src={url}
            controls
            preload="metadata"
            className="nodrag h-7 w-full"
          />
        );
      return null;
  }
}
