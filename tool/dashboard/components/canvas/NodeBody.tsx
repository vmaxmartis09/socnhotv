"use client";

import { Reveal } from "./Reveal";
import { fetchProjectPolicy, type ContentPolicy } from "@/lib/api/policy";
import { CORE_URL } from "@/lib/repositories/core";
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
import { useHubScope } from "@/lib/hub";
import { RefreshCw } from "@/components/ui/icons";
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
  /** Card Text: chế độ chỉnh sửa (mở rộng) */
  expanded?: boolean;
  /** Card nhân vật: mở bảng chọn nhân vật bên cạnh */
  onPickCharacter?: () => void;
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
function CharacterHero({ c, compact, detailed, onPick }: { c: Character; compact?: boolean; detailed?: boolean; onPick?: () => void }) {
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
        <button
          type="button"
          title="Mở hồ sơ nhân vật"
          aria-label="Mở hồ sơ nhân vật"
          onClick={(e) => {
            e.stopPropagation();
            useHubScope.getState().openTab("characters", null, c.id);
          }}
          className="nodrag text-sm font-semibold text-foreground underline-offset-2 hover:underline"
        >
          {c.name}
        </button>
        {onPick && (
          <button
            type="button"
            title="Đổi nhân vật"
            aria-label="Đổi nhân vật"
            onClick={(e) => {
              e.stopPropagation();
              onPick();
            }}
            className="nodrag mr-1 flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        )}
        <Chip title="Chiều cao">{c.heightCm} cm</Chip>
        <Chip title="Giọng">{c.voiceId || "—"}</Chip>
      </div>
      <Reveal show={!compact && Boolean(detailed)}>
        <div className="space-y-1.5">
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
        </div>
      </Reveal>
    </div>
  );
}

/** Chế độ xem card giọng đọc: rê chuột vào thì đọc — ưu tiên văn bản nhận từ node trước, nếu không thì văn bản của chính card. */
function VoiceHoverSpeaker({
  nodeId,
  ownText,
  voiceId,
  audioUrl,
}: {
  nodeId: string;
  ownText: string;
  voiceId?: string;
  audioUrl?: string;
}) {
  const nodes = useStudioStore((s: any) => s.nodes) as any[];
  const edges = useStudioStore((s: any) => s.edges) as any[];
  const [speaking, setSpeaking] = React.useState(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  const edge = edges.find((e) => e.target === nodeId && e.targetHandle === "text");
  const src = edge ? nodes.find((n) => n.id === edge.source) : undefined;
  const sp = src?.data?.params || {};
  const inputText: string = (src && (sp.content || sp.text || sp.prompt || src.data?.summaryText)) || "";
  const text = (inputText || ownText || "").trim();

  const stop = () => {
    audioRef.current?.pause();
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    setSpeaking(false);
  };
  const start = () => {
    // Không có file kết quả và không có lời thoại: phát mẫu giọng mặc định
    const sampleUrl = !audioUrl && !text ? `${CORE_URL}/voices/${voiceId || "soc-nho"}/sample` : undefined;
    const playUrl = audioUrl || sampleUrl;
    if (playUrl) {
      audioRef.current = audioRef.current?.src === playUrl ? audioRef.current : new Audio(playUrl);
      audioRef.current.onended = () => setSpeaking(false);
      audioRef.current.onerror = () => setSpeaking(false);
      audioRef.current.currentTime = 0;
      audioRef.current.play().then(() => setSpeaking(true)).catch(() => setSpeaking(false));
      return;
    }
    if (!text || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "vi-VN";
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
    setSpeaking(true);
  };
  React.useEffect(() => stop, []); // dừng khi card bị gỡ

  return (
    <div
      onMouseEnter={start}
      onMouseLeave={stop}
      title="Rê chuột để nghe"
      className={cn(
        "flex items-start gap-2 rounded-md border border-dashed p-2 text-xs transition-colors",
        speaking ? "border-brand bg-brand/5" : "border-border"
      )}
    >
      <Volume2 className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", speaking ? "animate-pulse text-brand" : "text-muted-foreground")} />
      <div className="min-w-0 flex-1">
        <p className={cn("line-clamp-3 break-words", text ? "text-foreground" : "text-muted-foreground")}>
          {text || "Chưa có lời thoại — rê chuột để nghe giọng mẫu"}
        </p>
        {voiceId && <span className="mt-1 block truncate text-[10px] text-muted-foreground">{voiceId}</span>}
      </div>
    </div>
  );
}

/** Dòng tóm tắt chính sách nội dung của dự án (dùng ở card Chính sách và Kiểm tra chất lượng). */
function PolicyBadge() {
  const projectId = useStudioStore((s: any) => s.activeProjectId) as string;
  const [pol, setPol] = React.useState<ContentPolicy | null | undefined>(undefined);
  React.useEffect(() => {
    let alive = true;
    fetchProjectPolicy(projectId).then((p) => alive && setPol(p));
    return () => {
      alive = false;
    };
  }, [projectId]);
  const rules = pol?.rules.filter((r) => r.enabled) || [];
  const terms = rules.reduce((n, r) => n + r.terms.length, 0);
  return (
    <div className="flex items-center gap-2 rounded-md border border-dashed border-border px-2 py-1.5 text-xs">
      <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <span className="min-w-0 flex-1 truncate text-foreground">
        {pol === undefined ? "Đang đọc chính sách…" : pol === null ? "Chưa đọc được chính sách" : pol.name}
      </span>
      {pol && (
        <span className="shrink-0 text-[12px] text-muted-foreground">
          {rules.length} quy tắc · {terms} từ
        </span>
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
  expanded,
  onPickCharacter,
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
          expanded={expanded}
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
          expanded={expanded}
        />
      );

    case "script":
      return (
        <div>
          <Reveal show={!expanded}>
            {lines.length > 0 ? (
              <ul className="space-y-0.5 text-xs text-foreground">
                {lines.slice(0, 4).map((l, i) => (
                  <li key={i} className="line-clamp-1">{l}</li>
                ))}
              </ul>
            ) : (
              <Empty icon={<ScrollText className="h-5 w-5" />} text="Chưa có phân cảnh" />
            )}
          </Reveal>
          <Reveal show={Boolean(expanded)}>
            <NodeScriptInput
              nodeId={nodeId}
              mode={p.mode}
              rawScript={p.rawScript}
              ideaText={p.text || p.content}
              targetSceneCount={p.targetSceneCount}
              targetDurationSec={p.targetDurationSec}
              connectedText={connectedInputs.includes("text")}
            />
          </Reveal>
        </div>
      );

    case "voice_tts":
      return (
        <div className="space-y-2">
          <Reveal show={Boolean(expanded)}>
            <NodeVoiceInput
              nodeId={nodeId}
              text={p.text}
              voiceId={p.voiceId}
              tempo={p.tempo}
              connectedText={connectedInputs.includes("text")}
            />
          </Reveal>
          {!expanded && (
            <VoiceHoverSpeaker
              nodeId={nodeId}
              ownText={typeof p.text === "string" ? p.text : ""}
              voiceId={p.voiceId}
              audioUrl={url && data.previewType === "audio" ? url : undefined}
            />
          )}
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
          {!url && !expanded && (
            <Empty icon={<Images className="h-6 w-6" />} text="Ảnh sẽ hiện ở đây" tall />
          )}
          <Reveal show={Boolean(expanded)}>
            <NodeImageGenInput
              nodeId={nodeId}
              prompt={p.prompt}
              referenceImages={p.referenceImages}
              aspectRatio={p.aspectRatio}
              model={p.model}
              connectedPrompt={connectedInputs.includes("prompt")}
            />
          </Reveal>
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
            <Reveal show={Boolean(expanded)}>
            <textarea
              rows={2}
              value={p.prompt || ""}
              onChange={(e) =>
                updateNodeParams(nodeId, { prompt: e.target.value })
              }
              placeholder="Prompt chuyển động video..."
              className="nodrag nowheel w-full rounded border border-border bg-card p-1.5 text-xs text-foreground placeholder:text-muted-foreground/60"
            />
            </Reveal>
          )}
        </div>
      );

    case "character":
      return (
        <div className="space-y-2">
          {character && <CharacterHero c={character} compact={compact} detailed={Boolean(expanded)} onPick={onPickCharacter} />}
        </div>
      );

    case "captions":
      return (
        <div className="space-y-2">
          <Reveal show={Boolean(expanded)}>
            <NodeCaptionsInput
              nodeId={nodeId}
              style={p.style}
              language={p.language}
            />
          </Reveal>
          {lines.length === 0 && !expanded && (
            <Empty icon={<ScrollText className="h-5 w-5" />} text="Chưa có phụ đề" />
          )}
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
          <Reveal show={Boolean(expanded)}>
            <NodeExportInput
              nodeId={nodeId}
              outputFileName={p.outputFileName}
              platforms={p.platforms}
              previewUrl={url}
            />
          </Reveal>
          {!expanded && !(url && data.previewType === "video") && (
            <div className="space-y-1 rounded-md border border-dashed border-border p-2 text-xs">
              <div className="truncate font-medium text-foreground">{p.outputFileName || "Chưa đặt tên file"}</div>
              {Array.isArray(p.platforms) && p.platforms.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {p.platforms.map((pl: string) => (
                    <Chip key={pl} title="Nền tảng">{pl}</Chip>
                  ))}
                </div>
              )}
            </div>
          )}
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

    case "policy":
      return (
        <div className="space-y-2">
          <PolicyBadge />
          <Reveal show={Boolean(expanded)}>
            <label className="block space-y-1 pt-1">
              <span className="text-[13px] text-muted-foreground">Từ khoá bổ sung riêng cho node này (mỗi dòng một mục)</span>
              <textarea
                rows={3}
                value={Array.isArray(p.extraTerms) ? p.extraTerms.join("\n") : ""}
                onChange={(e) => updateNodeParams(nodeId, { extraTerms: e.target.value.split("\n") })}
                className="nodrag nowheel w-full resize-y rounded-md border border-border bg-card p-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </label>
          </Reveal>
        </div>
      );

    case "quality_check":
    case "vision_analyze":
      if (nodeType === "quality_check")
        return (
          <div className="space-y-2">
            {url && data.previewType === "image" && <ImagePreview url={url} alt={nodeType} compact={compact} />}
            {lines.length === 0 && !(url && data.previewType === "image") && (
              <Empty icon={<ShieldCheck className="h-5 w-5" />} text="Chưa kiểm tra" />
            )}
            <PolicyBadge />
          </div>
        );
      if (url && data.previewType === "image")
        return <ImagePreview url={url} alt={nodeType} compact={compact} />;
      return lines.length > 0 ? null : (
        <Empty icon={<ShieldCheck className="h-5 w-5" />} text="Chưa phân tích" />
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
