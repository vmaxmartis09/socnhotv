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
import { usePreview } from "@/lib/preview";
import { fetchScriptData } from "@/lib/api/nodes";
import { fetchProjectOutputs } from "@/lib/core-api";
import { useHubScope } from "@/lib/hub";
import { RefreshCw, MorphIcon, Volume2Node, VolumeXNode, UsersNode } from "@/components/ui/icons";
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

/** Lời nhân vật đọc (tuỳ chỉnh) + nghe thử câu này bằng đúng giọng đã cấu hình (OmniVoice thật, ~15 giây). */
function SpeakTextBox({ text, onChange, voiceId }: { text: string; onChange: (t: string) => void; voiceId?: string }) {
  const projectId = useStudioStore((st: any) => st.activeProjectId) as string;
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState("");
  const ref = React.useRef<HTMLAudioElement | null>(null);
  React.useEffect(() => () => { ref.current?.pause(); }, []);
  // Trình duyệt chặn phát âm thanh nếu chờ API quá lâu sau cú bấm: "mở khoá" bằng đoạn lặng ngay lúc bấm.
  const SILENT = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";
  const say = async () => {
    const t = text.trim();
    if (!t || !voiceId) return;
    setBusy(true); setErr("");
    const a = new Audio(SILENT);
    ref.current?.pause();
    ref.current = a;
    try { await a.play(); } catch { /* bỏ qua */ }
    try {
      const r = await fetch(`${CORE_URL}/projects/${projectId}/voice/say`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: t, voiceId }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j?.detail || `Lỗi ${r.status}`);
      a.src = `${CORE_URL}${j.audioUrl}`;
      await a.play();
    } catch (e: any) { setErr(String(e?.message || e)); } finally { setBusy(false); }
  };
  return (
    <div className="nodrag nowheel space-y-1">
      <textarea
        value={text}
        onChange={(e) => onChange(e.target.value)}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
        rows={3}
        maxLength={400}
        placeholder="Gõ lời nhân vật sẽ đọc (bỏ trống = dùng văn bản nối vào cổng text)"
        className="w-full resize-none rounded-md border border-border bg-card px-2 py-1 text-[11px] leading-snug outline-none focus:border-foreground"
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={busy || !text.trim() || !voiceId}
          onClick={(e) => { e.stopPropagation(); void say(); }}
          className="inline-flex h-6 items-center gap-1 rounded-full border border-border px-2 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
        >
          <MorphIcon icon={Volume2Node} spring="snappy" size={12} />
          {busy ? `Đang đọc… (~${Math.max(5, Math.round(text.length / 3))}s)` : "Nghe thử câu này"}
        </button>
        <span className="text-[10px] text-muted-foreground">{text.length}/400</span>
      </div>
      {err && <p className="text-[10px] text-semantic-danger">{err}</p>}
    </div>
  );
}

/** Chip giọng: bấm để nghe mẫu giọng đã cấu hình của nhân vật (bấm lần nữa để dừng). */
function VoiceChip({ voiceId, sampleUrl }: { voiceId?: string; sampleUrl?: string }) {
  const ref = React.useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = React.useState(false);
  React.useEffect(() => () => { ref.current?.pause(); }, []);
  const url = sampleUrl ? (/^https?:/.test(sampleUrl) ? sampleUrl : `${CORE_URL}${sampleUrl}`) : "";
  if (!url) return <Chip title="Giọng">{voiceId || "—"}</Chip>;
  return (
    <button
      type="button"
      title={playing ? "Dừng nghe thử" : "Bấm để nghe thử giọng"}
      aria-label="Nghe thử giọng"
      onClick={(e) => {
        e.stopPropagation();
        if (playing) { ref.current?.pause(); setPlaying(false); return; }
        const a = ref.current ?? new Audio(url);
        ref.current = a;
        a.onended = () => setPlaying(false);
        a.onerror = () => setPlaying(false);
        a.currentTime = 0;
        a.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
      }}
      className="nodrag inline-flex h-6 items-center gap-1 rounded-full border border-border px-2 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      <MorphIcon icon={playing ? Volume2Node : VolumeXNode} spring="snappy" size={12} />
      {voiceId || "—"}
    </button>
  );
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
    <img decoding="async"
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
function CharacterHero({
  c,
  compact,
  detailed,
  onPick,
  speak,
}: {
  c: Character;
  compact?: boolean;
  detailed?: boolean;
  onPick?: () => void;
  /** Chức năng "Nói" của node Nhân vật (chỉ có khi Core khai báo chức năng speak) */
  speak?: { enabled: boolean; hasLines: boolean; onToggle: () => void; text: string; onTextChange: (t: string) => void };
}) {
  const gallery = c.referenceImages.slice(1, 5);
  return (
    <div className="space-y-1.5 pt-1">
      {c.referenceImages[0] ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img decoding="async" loading="lazy"
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
        <VoiceChip voiceId={c.voiceId} sampleUrl={c.sampleAudioUrl} />
        {speak && (
          <button
            type="button"
            aria-pressed={speak.enabled}
            title={
              speak.enabled
                ? "Đang bật Nói: nhân vật tự đọc câu của mình từ cổng lines của Kịch bản. Bấm để tắt."
                : "Bật Nói: nhân vật tự đọc lời thoại của mình trong kịch bản (thay cho node Giọng)"
            }
            onClick={(e) => {
              e.stopPropagation();
              speak.onToggle();
            }}
            className={cn(
              "nodrag inline-flex h-6 items-center gap-1 rounded-full border px-2 text-[11px] font-medium transition-colors",
              speak.enabled
                ? "border-foreground/20 bg-foreground text-background"
                : "border-border text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <MorphIcon icon={speak.enabled ? Volume2Node : VolumeXNode} spring="snappy" size={12} />
            Nói
          </button>
        )}
      </div>
      {speak?.enabled && !speak.hasLines && (
        <SpeakTextBox text={speak.text} onChange={speak.onTextChange} voiceId={c.voiceId} />
      )}
      {speak?.enabled && !speak.hasLines && (
        <p className="text-[10px] leading-snug text-muted-foreground">
          Nối cổng <span className="font-medium text-foreground">lines</span> của Kịch bản vào nhân vật, rồi nối cổng{" "}
          <span className="font-medium text-foreground">voice</span> sang <span className="font-medium text-foreground">voice_clips</span> của Dựng phim.
        </p>
      )}
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
                <img decoding="async"
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

/** Dàn diễn viên: hiện NGAY các nhân vật của tập đang chọn ở node Kịch bản nối vào (đổi tập là đổi theo, không cần chạy).
 *  Mỗi nhân vật là một thẻ gọn như node Nhân vật: ảnh DNA, tên, chiều cao, giọng, số câu thoại. */
const CAST_CACHE = new Map<string, { cast: { id: string | null; name: string }[]; lineCount: Record<string, number>; unmatched: string[] }>();

function CastPreview({ nodeId, data }: { nodeId: string; data: any }) {
  const projectId = useStudioStore((st: any) => st.activeProjectId) as string;
  const characters = useStudioStore((st: any) => st.characters) as Character[];
  const episodeId = useStudioStore((st: any) => {
    for (const e of st.edges) {
      if (e.target !== nodeId) continue;
      const src = st.nodes.find((n: any) => n.id === e.source);
      if (src?.data?.nodeType === "script" && src.data.params?.mode === "episode") return String(src.data.params.episodeId || "");
    }
    return "";
  });
  const include: string[] = data?.params?.include || [];
  const exclude: string[] = data?.params?.exclude || [];
  type CastView = { cast: { id: string | null; name: string }[]; lineCount: Record<string, number>; unmatched: string[] };
  const key = `${projectId}:${episodeId}`;
  // Giữ dàn nhân vật cũ (mờ đi) trong lúc tải dàn mới, và nhớ các tập đã xem -> đổi tập là đổi ngay, không nháy trống
  const [view, setView] = React.useState<CastView | null>(() => CAST_CACHE.get(key) || null);
  const [loading, setLoading] = React.useState(false);
  React.useEffect(() => {
    if (!episodeId) {
      setView(null);
      return;
    }
    const hit = CAST_CACHE.get(key);
    if (hit) {
      setView(hit);
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(true);
    fetchScriptData(projectId, episodeId).then((d: any) => {
      if (!alive) return;
      const sc = d?.script;
      const counts: Record<string, number> = {};
      for (const sh of d?.shots || []) {
        if (sh.characterId && sh.dialogue) counts[sh.characterId] = (counts[sh.characterId] || 0) + 1;
      }
      const v: CastView = {
        cast: (sc?.cast || []).map((c: any) => ({ id: c.id || null, name: c.name })),
        lineCount: counts,
        unmatched: sc?.unmatched || [],
      };
      if (d) CAST_CACHE.set(key, v);
      setView(v);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [key, projectId, episodeId]);
  const cast = view?.cast ?? null;
  const lineCount = view?.lineCount ?? {};
  const unmatched = view?.unmatched ?? [];
  if (!episodeId) {
    return (
      <p className="text-xs text-muted-foreground">
        Nối cổng <span className="font-medium text-foreground">lines</span> của Kịch bản (chế độ Kịch bản tập) để tự lấy nhân vật theo tập.
      </p>
    );
  }
  const members = [
    ...(cast || []).filter((c) => !(c.id && exclude.includes(c.id))),
    ...include.filter((id) => !(cast || []).some((c) => c.id === id)).map((id) => ({ id, name: id })),
  ];
  return (
    <div className="space-y-1.5">
      <div className="text-[11px] text-muted-foreground">
        Tập <span className="font-mono text-foreground">{episodeId.replace(/^ep(\d+)-.*/, "$1")}</span> · {members.length} nhân vật
      </div>
      {cast === null && <span className="text-xs text-muted-foreground">Đang đọc kịch bản…</span>}
      <div className={cn("space-y-1.5 transition-opacity duration-200", loading && "opacity-50")}>
        {members.map((m) => {
          const ch = m.id ? characters.find((c) => c.id === m.id) : undefined;
          return (
            <div key={m.id || m.name} className="flex items-center gap-2 rounded-lg border border-border bg-card/60 p-1.5">
              {ch?.referenceImages?.[0] ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  decoding="async"
                  loading="lazy"
                  src={ch.referenceImages[0]}
                  alt={ch.name}
                  className="h-14 w-14 shrink-0 rounded-md border border-border bg-muted/20 object-cover object-top"
                />
              ) : (
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-dashed border-semantic-warning text-[10px] text-semantic-warning">
                  chưa có
                </div>
              )}
              <div className="min-w-0 flex-1 space-y-0.5">
                <button
                  type="button"
                  title="Mở hồ sơ nhân vật"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (m.id) useHubScope.getState().openTab("characters", null, m.id);
                  }}
                  className="nodrag block max-w-full truncate text-left text-[13px] font-semibold text-foreground underline-offset-2 hover:underline"
                >
                  {ch?.name || m.name}
                </button>
                <div className="flex flex-wrap items-center gap-1">
                  {ch && <Chip title="Chiều cao">{ch.heightCm} cm</Chip>}
                  {ch && <Chip title="Giọng">{ch.voiceId || "—"}</Chip>}
                  {m.id && lineCount[m.id] ? <Chip title="Số câu thoại">{lineCount[m.id]} câu</Chip> : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {unmatched.length > 0 && <div className="text-[11px] text-semantic-warning">Chưa ghép được: {unmatched.join(", ")}</div>}
      {members.some((m) => m.id) && (
        <button
          type="button"
          title="Tách thành từng node Nhân vật để xem và chỉnh riêng (nhân vật cố định theo tập hiện tại). Hoàn tác bằng Ctrl+Z."
          onClick={(e) => {
            e.stopPropagation();
            const ids = members.map((m) => m.id).filter(Boolean) as string[];
            (useStudioStore.getState() as any).expandCastToCharacters(nodeId, ids);
          }}
          className="nodrag flex w-full items-center justify-center gap-1.5 rounded-md border border-border bg-card px-2 py-1 text-[11px] font-medium text-foreground transition-colors hover:bg-accent"
        >
          <MorphIcon icon={UsersNode} size={12} />
          Phân rã thành {members.filter((m) => m.id).length} node nhân vật
        </button>
      )}
    </div>
  );
}

/** Poster của video tập: output/<tập>/<tên>.mp4 -> output/<tập>/thumb.jpg (bộ Xuất của G3 luôn ghi thumb.jpg) */
function posterFor(url: string): string | undefined {
  return /\/output\/[^/]+\/[^/]+\.mp4(\?.*)?$/.test(url) ? url.replace(/[^/]+\.mp4(\?.*)?$/, "thumb.jpg") : undefined;
}

/** Thành phẩm mới nhất của tập đang chọn (output/<tập>/video.json qua GET /projects/{id}/outputs):
 * poster + nút "Xem & tua" mở PreviewPane. Chạy thật thì node Xuất không có previewUrl video nên lấy từ đây. */
function EpisodeOutputPreview({ status, outputFileName }: { status?: string; outputFileName?: string }) {
  const projectId = useStudioStore((s) => s.activeProjectId);
  const episodeId = useStudioStore(
    (s) =>
      (s.nodes.find((n) => n.data?.nodeType === "script" && n.data?.params?.mode === "episode")?.data?.params?.episodeId as
        | string
        | undefined) || ""
  );
  const [out, setOut] = React.useState<any | null>(null);
  React.useEffect(() => {
    if (!projectId || !episodeId) return setOut(null);
    let alive = true;
    fetchProjectOutputs(projectId).then((list) => {
      if (!alive) return;
      const want = (outputFileName || "").trim();
      const hit = (list || []).find((o: any) => {
        const v = String(o?.files?.video || "");
        return v.endsWith(`/${episodeId}.mp4`) || (want && v.endsWith(`/${want}`) && String(o?.slug || "").startsWith(episodeId));
      });
      setOut(hit || null);
    });
    return () => {
      alive = false;
    };
  }, [projectId, episodeId, outputFileName, status]);
  if (!out || !projectId) return null;
  const base = `${CORE_URL}/projects/${encodeURIComponent(projectId)}/`;
  const videoUrl = base + String(out.files.video);
  const thumbUrl = out.files.thumb ? base + String(out.files.thumb) : undefined;
  const dur = Number(out.duration_s) || 0;
  const ev = out.episodeVerify as { pass1to5?: boolean; verdict?: string } | undefined;
  const caption = [out.engine ? `engine: ${out.engine}` : null, ev?.verdict || "chưa chạy verify_episode"].filter(Boolean).join(" · ");
  const open = () =>
    usePreview.getState().open({
      kind: "video",
      title: out.title || episodeId,
      index: 0,
      items: [{ url: videoUrl, name: String(out.files.video), poster: thumbUrl, caption }],
    });
  return (
    <div className="space-y-1" data-testid="episode-output">
      <button
        type="button"
        onClick={open}
        title="Xem và tua thành phẩm ngay trong Studio"
        className="nodrag group relative block w-full overflow-hidden rounded-md bg-black"
      >
        {thumbUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img decoding="async" loading="lazy" src={thumbUrl} alt="" className="aspect-video w-full object-cover opacity-90 group-hover:opacity-100" />
        )}
        <span className="absolute inset-0 flex items-center justify-center">
          <span className="flex items-center gap-1 rounded-full bg-black/70 px-3 py-1 text-[11px] font-semibold text-white">
            <Film className="h-3 w-3" /> Xem & tua
          </span>
        </span>
      </button>
      <div className="flex flex-wrap gap-1 text-[10px] text-muted-foreground tnum">
        <span>{String(out.files.video).split("/").pop()}</span>
        {dur > 0 && <span>· {Math.floor(dur / 60)}:{String(Math.round(dur % 60)).padStart(2, "0")}</span>}
        {ev && <span className={ev.pass1to5 ? "text-semantic-success" : "text-semantic-warning"}>· {ev.pass1to5 ? "verify 1–5 ĐẠT" : "verify CHƯA ĐẠT"}</span>}
      </div>
    </div>
  );
}

/** Tải "gói shot" (ảnh khung đầu + prompt video từng shot chính) để làm clip tay rồi thả vào clips/ (C5). */
function ShotPackLink({ episodeId }: { episodeId: string }) {
  const projectId = useStudioStore((s) => s.activeProjectId);
  if (!projectId) return null;
  const href = `${CORE_URL}/data/projects/${encodeURIComponent(projectId)}/episodes/${encodeURIComponent(episodeId)}/shot-pack`;
  return (
    <a
      href={href}
      download={`${episodeId}_shot-pack.zip`}
      title="ZIP gồm ảnh khung đầu + prompt video của các shot chính (priority 1). Làm clip xong đặt tên S07.mp4 và thả vào content/episodes/<tập>/clips/"
      data-testid="shot-pack-download"
      className="nodrag mt-2 flex w-full items-center justify-center gap-1 rounded-md border border-dashed border-border py-1 text-[11px] font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
    >
      <Download className="h-3 w-3" />
      Gói shot làm clip tay (ZIP)
    </a>
  );
}

export const NodeBody = React.memo(function NodeBody({
  nodeType,
  nodeId,
  data,
  character,
  connectedInputs,
  compact,
  expanded,
  onPickCharacter,
}: Props) {
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const hasSpeakCapability = useStudioStore((s) =>
    Boolean(s.nodeCatalog.find((d) => d.typeName === nodeType)?.capabilities?.some((c) => c.name === "speak"))
  );
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
                  <li key={`${nodeId}-line-${i}-${l.slice(0, 10)}`} className="line-clamp-1">{l}</li>
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
              episodeId={p.episodeId}
              granularity={p.granularity}
              ideaText={p.text || p.content}
              targetSceneCount={p.targetSceneCount}
              targetDurationSec={p.targetDurationSec}
              connectedText={connectedInputs.includes("text")}
            />
          </Reveal>
          {p.mode === "episode" && p.episodeId && <ShotPackLink episodeId={String(p.episodeId)} />}
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

    case "cast":
      return <CastPreview nodeId={nodeId} data={data} />;

    case "character":
      return (
        <div className="space-y-2">
          {character && (
            <CharacterHero
              c={character}
              compact={compact}
              detailed={Boolean(expanded)}
              onPick={onPickCharacter}
              speak={
                hasSpeakCapability
                  ? {
                      enabled: Boolean(p.speak?.enabled),
                      hasLines: connectedInputs.includes("lines"),
                      onToggle: () =>
                        updateNodeParams(nodeId, { speak: { ...(p.speak || {}), enabled: !p.speak?.enabled } }),
                      text: String(p.speak?.text || ""),
                      onTextChange: (t: string) => updateNodeParams(nodeId, { speak: { ...(p.speak || {}), text: t } }),
                    }
                  : undefined
              }
            />
          )}
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
                <li key={`${nodeId}-cap-${i}-${l.slice(0, 10)}`} className="truncate text-muted-foreground">
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
          {!(url && data.previewType === "video") && <EpisodeOutputPreview status={data.status} outputFileName={p.outputFileName} />}
          {url && data.previewType === "video" && (
            <>
              <video
                src={url}
                controls
                preload="metadata"
                poster={posterFor(url)}
                className="nodrag max-h-48 w-full rounded-md bg-black object-contain"
              />
              <button
                type="button"
                title="Mở video lớn để xem và tua"
                data-testid="export-open-preview"
                onClick={() =>
                  usePreview.getState().open({
                    kind: "video",
                    title: p.outputFileName || "Thành phẩm",
                    index: 0,
                    items: [{ url, name: p.outputFileName || url.split("/").pop() || "video", poster: posterFor(url) }],
                  })
                }
                className="nodrag flex w-full items-center justify-center gap-1 rounded-md border border-border py-1 text-[11px] font-medium text-foreground hover:bg-accent"
              >
                <Film className="h-3 w-3" />
                Xem lớn
              </button>
            </>
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
});
