"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { enterOnce } from "@/lib/motion";
import {
  Wrench,
  Play,
  Upload,
  Download,
  FolderOpen,
  Image as ImageIcon,
  Mic,
  Music,
  X,
  Check,
  AlertTriangle,
} from "@/components/ui/icons";
import { AiLoading } from "@/components/ui/AiLoading";
import { cn } from "@/lib/utils";

/* ───────────────────────── Kiểu dữ liệu ───────────────────────── */

interface ToolItem {
  id: string;
  name: string;
  version: string;
  status: "verified" | "installed" | "planned" | "broken";
  license?: { code: string; commercial_ok: boolean };
  requires_gpu: boolean;
  requires_ffmpeg: boolean;
}
interface Targets {
  projects: { id: string; name: string }[];
  characters: Record<string, { id: string; name: string }[]>;
  active: string | null;
  sharedDir: string;
}
interface RunOut {
  path: string;
  kind: string;
}
type SubTab = "tools" | "cutouts" | "audio" | "voices";

const EASE = [0.22, 1, 0.36, 1] as const;
const previewUrl = (p: string, download = false) =>
  `/api/toolbox/preview?path=${encodeURIComponent(p)}${download ? "&download=1" : ""}`;
const fileName = (p: string) => p.split(/[\\/]/).pop() || p;

async function uploadFile(file: File): Promise<{ path: string; name: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/toolbox/upload", { method: "POST", body: fd });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || "Tải lên thất bại");
  return { path: j.path, name: j.name };
}

async function runTool(toolId: string, params: Record<string, unknown>, inputs: string[]) {
  const r = await fetch("/api/toolbox", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ toolId, inData: { params, inputs } }),
  });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || j.result?.error?.message || "Tool báo lỗi");
  return j.result as { outputs: RunOut[]; elapsed_s?: number; warnings?: string[] };
}

/* ───────────────────────── Thành phần nhỏ dùng chung ───────────────────────── */

/** Vùng nhập file: bấm, kéo-thả hoặc dán (Ctrl+V). */
function Dropzone({
  accept,
  icon,
  title,
  hint,
  busy,
  onFile,
}: {
  accept: string;
  icon: React.ReactNode;
  title: string;
  hint: string;
  busy?: boolean;
  onFile: (f: File) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={title}
      onClick={() => !busy && ref.current?.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && ref.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f && !busy) onFile(f);
      }}
      onPaste={(e) => {
        const f = e.clipboardData.files?.[0];
        if (f && !busy) onFile(f);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-start gap-1 rounded-xl border border-dashed p-3 text-left transition-colors",
        over ? "border-brand bg-brand/5" : "border-border hover:border-foreground/30 hover:bg-accent/40",
        busy && "pointer-events-none opacity-60"
      )}
    >
      <span className="flex items-center gap-2 text-[12px] font-medium text-foreground">
        <span className="text-muted-foreground [&_svg]:h-4 [&_svg]:w-4">{icon}</span>
        {title}
      </span>
      <span className="text-[11px] text-muted-foreground">{hint}</span>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
    </div>
  );
}

/** Tải về + Lưu vào dự án / nhân vật (chỉ sao chép, không ghi đè). */
function SaveBar({
  files,
  targets,
  onSaved,
}: {
  files: { label: string; path: string }[];
  targets: Targets | null;
  onSaved?: () => void;
}) {
  const [fileIdx, setFileIdx] = useState(0);
  const [where, setWhere] = useState<"project" | "character">("project");
  const [projectId, setProjectId] = useState("");
  const [characterId, setCharacterId] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    if (targets && !projectId) setProjectId(targets.active || targets.projects[0]?.id || "");
  }, [targets, projectId]);
  const chars = (targets && targets.characters[projectId]) || [];
  useEffect(() => {
    if (where === "character" && !chars.some((c) => c.id === characterId)) setCharacterId(chars[0]?.id || "");
  }, [where, projectId, chars, characterId]);

  const file = files[Math.min(fileIdx, files.length - 1)];
  if (!file) return null;

  const save = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const r = await fetch("/api/toolbox/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          src: file.path,
          projectId,
          characterId: where === "character" ? characterId : undefined,
        }),
      });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error || "Lưu thất bại");
      setMsg({ ok: true, text: `Đã lưu: ${j.relative}` });
      onSaved?.();
    } catch (e: any) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

  const sel = "h-7 min-w-0 rounded-md border border-input bg-card px-1.5 text-[11px] text-foreground";
  return (
    <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-2">
      <div className="flex flex-wrap items-center gap-1.5">
        {files.length > 1 && (
          <select aria-label="Chọn file" value={fileIdx} onChange={(e) => setFileIdx(Number(e.target.value))} className={sel}>
            {files.map((f, i) => (
              <option key={f.path} value={i}>
                {f.label}
              </option>
            ))}
          </select>
        )}
        <a
          href={previewUrl(file.path, true)}
          download
          data-tip="Tải file về máy"
          aria-label="Tải về"
          className="flex h-7 items-center gap-1 rounded-md border border-border px-2 text-[11px] font-medium text-foreground transition-all hover:bg-accent active:scale-95"
        >
          <Download className="h-3.5 w-3.5" />
          Tải về
        </a>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        <select aria-label="Lưu vào" value={where} onChange={(e) => setWhere(e.target.value as any)} className={sel}>
          <option value="project">Lưu vào dự án</option>
          <option value="character">Lưu vào nhân vật</option>
        </select>
        <select aria-label="Dự án" value={projectId} onChange={(e) => setProjectId(e.target.value)} className={sel}>
          {(targets?.projects || []).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {where === "character" && (
          <select aria-label="Nhân vật" value={characterId} onChange={(e) => setCharacterId(e.target.value)} className={sel}>
            {chars.length === 0 && <option value="">— chưa có nhân vật —</option>}
            {chars.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}
        <button
          type="button"
          onClick={save}
          disabled={saving || !projectId || (where === "character" && !characterId)}
          data-tip={where === "character" ? "Sao chép vào thư mục toolbox của nhân vật" : "Sao chép vào thư viện của dự án"}
          className="flex h-7 items-center gap-1 rounded-md bg-primary px-2.5 text-[11px] font-medium text-primary-foreground transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <FolderOpen className="h-3.5 w-3.5" />
          {saving ? "Đang lưu…" : "Lưu"}
        </button>
      </div>
      {msg && (
        <p className={cn("flex items-start gap-1 text-[11px]", msg.ok ? "text-semantic-success" : "text-semantic-danger")}>
          {msg.ok ? <Check className="mt-0.5 h-3 w-3 shrink-0" /> : <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />}
          <span className="break-all">{msg.text}</span>
        </p>
      )}
    </div>
  );
}

function ErrorLine({ text, onClose }: { text: string; onClose: () => void }) {
  return (
    <div className="flex items-start gap-1.5 rounded-lg border border-semantic-danger/30 bg-semantic-danger/5 p-2 text-[11px] text-semantic-danger">
      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <span className="min-w-0 flex-1 break-words">{text}</span>
      <button type="button" aria-label="Đóng" onClick={onClose} className="shrink-0 active:scale-95">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

const checker =
  "rounded-lg border border-border bg-[radial-gradient(hsl(var(--border))_1px,transparent_1px)] [background-size:12px_12px] p-2 flex items-center justify-center";

/* ───────────────────────── Không gian làm việc: Tách nền ───────────────────────── */

function BgRemoveWorkspace({ targets, onDone }: { targets: Targets | null; onDone: () => void }) {
  const [src, setSrc] = useState<{ path: string; name: string } | null>(null);
  const [busy, setBusy] = useState<"upload" | "run" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [outs, setOuts] = useState<RunOut[] | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  const pick = async (f: File) => {
    setError(null);
    setOuts(null);
    setBusy("upload");
    try {
      setSrc(await uploadFile(f));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };
  const run = async () => {
    if (!src) return;
    setError(null);
    setBusy("run");
    try {
      const r = await runTool("bg-remove", { model: "u2net" }, [src.path]);
      setOuts(r.outputs);
      setElapsed(r.elapsed_s ?? null);
      onDone();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };
  const cutout = outs?.find((o) => o.kind === "cutout");
  const mask = outs?.find((o) => o.kind === "mask");

  return (
    <div className="space-y-2.5">
      <Dropzone
        accept="image/png,image/jpeg,image/webp"
        icon={<ImageIcon />}
        title={src ? `Ảnh: ${src.name} — bấm để đổi` : "Nhập ảnh cần tách nền"}
        hint="Bấm, kéo-thả hoặc dán ảnh (PNG, JPG, WEBP)"
        busy={busy !== null}
        onFile={pick}
      />
      {error && <ErrorLine text={error} onClose={() => setError(null)} />}
      {src && (
        <div className="grid grid-cols-2 gap-2">
          <figure className="space-y-1">
            <figcaption className="text-[10px] text-muted-foreground">Ảnh gốc</figcaption>
            <div className={checker}>
              <img src={previewUrl(src.path)} alt="Ảnh gốc" className="max-h-44 object-contain" />
            </div>
          </figure>
          <figure className="space-y-1">
            <figcaption className="text-[10px] text-muted-foreground">Đã tách nền {elapsed ? `· ${elapsed.toFixed(1)}s` : ""}</figcaption>
            <div className={cn(checker, "min-h-[96px]")}>
              {busy === "run" ? (
                <AiLoading label="Đang tách nền…" lines={0} />
              ) : cutout ? (
                <img src={previewUrl(cutout.path)} alt="Ảnh đã tách nền" className="max-h-44 object-contain" />
              ) : (
                <span className="text-[11px] text-muted-foreground">Chưa chạy</span>
              )}
            </div>
          </figure>
        </div>
      )}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={run}
          disabled={!src || busy !== null}
          data-tip={src ? "Chạy tách nền bằng rembg trên CPU (khoảng 20–30 giây)" : "Nhập ảnh trước"}
          className="flex h-8 items-center gap-1.5 rounded-md bg-brand px-3 text-[12px] font-medium text-white transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          {busy === "run" ? "Đang chạy…" : "Tách nền"}
        </button>
        {busy === "upload" && <span className="text-[11px] text-muted-foreground">Đang tải ảnh lên…</span>}
      </div>
      {cutout && (
        <SaveBar
          targets={targets}
          files={[
            { label: "Ảnh tách nền (PNG)", path: cutout.path },
            ...(mask ? [{ label: "Mặt nạ (mask)", path: mask.path }] : []),
          ]}
        />
      )}
    </div>
  );
}

/* ───────────────────────── Không gian làm việc: Âm thanh / giọng ───────────────────────── */

function AudioWorkspace({ targets, onDone }: { targets: Targets | null; onDone: () => void }) {
  const [src, setSrc] = useState<{ path: string; name: string } | null>(null);
  const [busy, setBusy] = useState<"upload" | "run" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState("vi");
  const [outs, setOuts] = useState<RunOut[] | null>(null);
  const [text, setText] = useState<string>("");

  const pick = async (f: File) => {
    setError(null);
    setOuts(null);
    setText("");
    setBusy("upload");
    try {
      setSrc(await uploadFile(f));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };
  const run = async () => {
    if (!src) return;
    setError(null);
    setBusy("run");
    try {
      const r = await runTool("stt-align", { model_size: "small", language: lang }, [src.path]);
      setOuts(r.outputs);
      const t = r.outputs.find((o) => o.kind === "word_timings");
      if (t) {
        const j = await fetch(previewUrl(t.path)).then((x) => x.json());
        setText(j.text || (j.words || []).map((w: any) => w.word || w.text).join(" "));
      }
      onDone();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const files = [
    ...(src ? [{ label: "File âm thanh gốc", path: src.path }] : []),
    ...(outs || []).map((o) => ({ label: o.kind === "subtitles_srt" ? "Phụ đề (.srt)" : "Canh từng từ (.json)", path: o.path })),
  ];

  return (
    <div className="space-y-2.5">
      <Dropzone
        accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac"
        icon={<Music />}
        title={src ? `Âm thanh: ${src.name} — bấm để đổi` : "Nhập mẫu giọng / file âm thanh"}
        hint="Bấm, kéo-thả hoặc dán (MP3, WAV, M4A, OGG, FLAC)"
        busy={busy !== null}
        onFile={pick}
      />
      {error && <ErrorLine text={error} onClose={() => setError(null)} />}
      {src && <audio controls src={previewUrl(src.path)} className="h-9 w-full" />}
      <div className="flex flex-wrap items-center gap-2">
        <select
          aria-label="Ngôn ngữ"
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          className="h-8 rounded-md border border-input bg-card px-1.5 text-[11px]"
        >
          <option value="vi">Tiếng Việt</option>
          <option value="en">English</option>
        </select>
        <button
          type="button"
          onClick={run}
          disabled={!src || busy !== null}
          data-tip={src ? "Phiên âm và canh từng từ (CPU, khoảng 10–30 giây)" : "Nhập âm thanh trước"}
          className="flex h-8 items-center gap-1.5 rounded-md bg-brand px-3 text-[12px] font-medium text-white transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          {busy === "run" ? "Đang phiên âm…" : "Phiên âm + canh từ"}
        </button>
      </div>
      {busy === "run" && <AiLoading label="Đang nghe và canh từng từ…" lines={2} />}
      {text && <p className="rounded-lg bg-muted/50 p-2.5 text-[12px] leading-relaxed">“{text}”</p>}
      {files.length > 0 && <SaveBar targets={targets} files={files} />}
    </div>
  );
}

/* ───────────────────────── Panel chính ───────────────────────── */

export function ToolboxPanel() {
  const [sub, setSub] = useState<SubTab>("tools");
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [vaults, setVaults] = useState<{ cutouts: any[]; audios: any[]; voices: any[] }>({ cutouts: [], audios: [], voices: [] });
  const [targets, setTargets] = useState<Targets | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>("bg-remove");
  const [checking, setChecking] = useState(false);
  const [checkMsg, setCheckMsg] = useState<string | null>(null);
  const [saveFor, setSaveFor] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [a, b, c] = await Promise.all([
        fetch("/api/toolbox?action=list").then((r) => r.json()),
        fetch("/api/toolbox?action=vaults").then((r) => r.json()),
        fetch("/api/toolbox?action=targets").then((r) => r.json()),
      ]);
      if (a.ok) setTools(a.tools);
      if (b.ok) setVaults(b.vaults);
      if (c.ok) setTargets(c);
      setLoadError(a.ok ? null : a.error || "Không đọc được danh mục công cụ");
    } catch (e: any) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);

  const checkFfmpeg = async () => {
    setChecking(true);
    setCheckMsg(null);
    try {
      const r = await runTool("ffmpeg-bin", {}, []);
      setCheckMsg(`Sẵn sàng: ${r.outputs.map((o) => fileName(o.path)).join(", ")}`);
    } catch (e: any) {
      setCheckMsg(`Lỗi: ${e.message}`);
    } finally {
      setChecking(false);
    }
  };

  const tabs: { id: SubTab; label: string; count: number }[] = [
    { id: "tools", label: "Công cụ", count: tools.length },
    { id: "cutouts", label: "Tách nền", count: vaults.cutouts.length },
    { id: "audio", label: "Canh từ", count: vaults.audios.length },
    { id: "voices", label: "Giọng", count: vaults.voices.length },
  ];

  const sectionAnim = (key: string) => ({
    initial: enterOnce(key, { opacity: 0 }),
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.18, ease: EASE },
  });

  return (
    <div className="flex h-full flex-col overflow-hidden bg-background text-left text-foreground">
      <div className="shrink-0 space-y-1 border-b border-border p-3">
        <div className="flex items-center gap-2">
          <span className="rounded bg-brand/10 p-1 text-brand">
            <Wrench className="h-4 w-4" />
          </span>
          <h2 className="text-[14px] font-semibold tracking-tight">Toolbox cục bộ</h2>
        </div>
        <p className="text-[12px] text-muted-foreground">Nhập file, chạy tool ngay tại đây, rồi tải về hoặc lưu vào dự án / nhân vật.</p>
        <div className="flex flex-wrap items-center gap-1 pt-1.5">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setSub(t.id)}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors active:scale-95",
                sub === t.id ? "bg-accent font-semibold text-foreground" : "text-muted-foreground hover:bg-accent/50"
              )}
            >
              {t.label}
              <span className="text-[10px] opacity-70">({t.count})</span>
            </button>
          ))}
        </div>
      </div>

      <div className="scroll-quiet flex-1 space-y-3 overflow-y-auto p-3">
        {loading ? (
          <AiLoading label="Đang quét danh mục công cụ…" lines={3} />
        ) : (
          <AnimatePresence mode="wait" initial={false}>
            {loadError && <ErrorLine text={loadError} onClose={() => setLoadError(null)} />}

            {/* ── CÔNG CỤ ── */}
            {sub === "tools" && (
              <motion.div key="tools" {...sectionAnim("tb-tools")} className="space-y-3">
                {tools.length === 0 && !loadError && (
                  <div className="rounded-xl border border-dashed border-border p-4 text-[12px] text-muted-foreground">
                    Chưa có công cụ nào trong <code>tool/toolbox/tools/</code>.
                  </div>
                )}
                {tools.map((tool) => {
                  const ready = tool.status === "verified" || tool.status === "installed";
                  const expanded = open === tool.id;
                  return (
                    <div key={tool.id} className={cn("space-y-2.5 rounded-xl border bg-card p-3 transition-colors", expanded ? "border-foreground/25" : "border-border")}>
                      <button
                        type="button"
                        onClick={() => setOpen(expanded ? null : tool.id)}
                        className="flex w-full items-start justify-between gap-2 text-left"
                        aria-expanded={expanded}
                      >
                        <span className="space-y-0.5">
                          <span className="flex items-center gap-1.5">
                            <span className="text-[13px] font-medium">{tool.name}</span>
                            <span className="rounded bg-muted px-1.5 text-[10px] text-muted-foreground">v{tool.version}</span>
                          </span>
                          <span className="block font-mono text-[11px] text-muted-foreground">{tool.id}</span>
                        </span>
                        <span
                          className={cn(
                            "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                            tool.status === "verified" ? "bg-semantic-success/10 text-semantic-success" : tool.status === "installed" ? "bg-brand/10 text-brand" : "bg-muted text-muted-foreground"
                          )}
                        >
                          {tool.status.toUpperCase()}
                        </span>
                      </button>
                      <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-muted-foreground">
                        <span className="rounded bg-muted px-1.5 py-0.5">{tool.requires_gpu ? "Cần GPU" : "Chạy CPU"}</span>
                        {tool.requires_ffmpeg && <span className="rounded bg-muted px-1.5 py-0.5">FFmpeg</span>}
                        {tool.license?.code && <span className="rounded bg-muted px-1.5 py-0.5">{tool.license.code}</span>}
                      </div>

                      {expanded && ready && tool.id === "bg-remove" && <BgRemoveWorkspace targets={targets} onDone={refresh} />}
                      {expanded && ready && tool.id === "stt-align" && <AudioWorkspace targets={targets} onDone={refresh} />}
                      {expanded && ready && tool.id === "ffmpeg-bin" && (
                        <div className="space-y-2">
                          <p className="text-[11px] text-muted-foreground">Bản ffmpeg dùng chung cho mọi tool (không sửa PATH hệ thống).</p>
                          <button
                            type="button"
                            onClick={checkFfmpeg}
                            disabled={checking}
                            className="flex h-8 items-center gap-1.5 rounded-md bg-brand px-3 text-[12px] font-medium text-white transition-all hover:opacity-90 active:scale-95 disabled:opacity-40"
                          >
                            <Check className="h-3.5 w-3.5" />
                            {checking ? "Đang kiểm tra…" : "Kiểm tra / cài"}
                          </button>
                          {checkMsg && <p className="break-all text-[11px] text-muted-foreground">{checkMsg}</p>}
                        </div>
                      )}
                      {expanded && !ready && (
                        <p className="text-[11px] text-muted-foreground">Công cụ chưa sẵn sàng (trạng thái: {tool.status}).</p>
                      )}
                    </div>
                  );
                })}
              </motion.div>
            )}

            {/* ── KHO TÁCH NỀN ── */}
            {sub === "cutouts" && (
              <motion.div key="cutouts" {...sectionAnim("tb-cutouts")} className="space-y-3">
                {vaults.cutouts.length === 0 ? (
                  <div className="space-y-1 rounded-xl border border-dashed border-border p-4">
                    <ImageIcon className="h-5 w-5 text-muted-foreground" />
                    <p className="text-[12px] font-medium">Chưa có ảnh tách nền</p>
                    <button type="button" onClick={() => { setSub("tools"); setOpen("bg-remove"); }} className="text-[11px] text-brand hover:underline">
                      Tách nền một ảnh ngay
                    </button>
                  </div>
                ) : (
                  vaults.cutouts.map((item) => (
                    <div key={item.id} className="space-y-2 rounded-xl border border-border bg-card p-3">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-medium">#{item.id}</span>
                        <span className="text-muted-foreground">
                          {item.metadata?.width}×{item.metadata?.height}
                        </span>
                      </div>
                      <div className={checker}>
                        <img src={previewUrl(item.files?.cutout || "")} alt="Ảnh tách nền" className="max-h-44 object-contain" onError={(e) => ((e.target as HTMLElement).style.display = "none")} />
                      </div>
                      <p className="truncate text-[10px] text-muted-foreground" title={item.source}>
                        Nguồn: {item.source}
                      </p>
                      {saveFor === `c${item.id}` ? (
                        <SaveBar
                          targets={targets}
                          files={[
                            { label: "Ảnh tách nền (PNG)", path: item.files?.cutout },
                            ...(item.files?.mask ? [{ label: "Mặt nạ (mask)", path: item.files.mask }] : []),
                          ]}
                        />
                      ) : (
                        <button type="button" onClick={() => setSaveFor(`c${item.id}`)} className="flex h-7 items-center gap-1 rounded-md border border-border px-2 text-[11px] font-medium transition-all hover:bg-accent active:scale-95">
                          <FolderOpen className="h-3.5 w-3.5" />
                          Tải về / Lưu vào…
                        </button>
                      )}
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {/* ── KHO CANH TỪ ── */}
            {sub === "audio" && (
              <motion.div key="audio" {...sectionAnim("tb-audio")} className="space-y-3">
                {vaults.audios.length === 0 ? (
                  <div className="space-y-1 rounded-xl border border-dashed border-border p-4">
                    <Mic className="h-5 w-5 text-muted-foreground" />
                    <p className="text-[12px] font-medium">Chưa có bản phiên âm</p>
                    <button type="button" onClick={() => { setSub("tools"); setOpen("stt-align"); }} className="text-[11px] text-brand hover:underline">
                      Phiên âm một file âm thanh ngay
                    </button>
                  </div>
                ) : (
                  vaults.audios.map((item) => (
                    <div key={item.id} className="space-y-2 rounded-xl border border-border bg-card p-3">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-medium">#{item.id}</span>
                        <span className="text-muted-foreground">
                          {item.metadata?.duration}s · {String(item.metadata?.language || "").toUpperCase()}
                        </span>
                      </div>
                      <p className="rounded-lg bg-muted/50 p-2.5 text-[12px] leading-relaxed">“{item.metadata?.text_preview}”</p>
                      {saveFor === `a${item.id}` ? (
                        <SaveBar
                          targets={targets}
                          files={[
                            ...(item.files?.timings ? [{ label: "Canh từng từ (.json)", path: item.files.timings }] : []),
                            ...(item.files?.subtitles ? [{ label: "Phụ đề (.srt)", path: item.files.subtitles }] : []),
                          ]}
                        />
                      ) : (
                        <button type="button" onClick={() => setSaveFor(`a${item.id}`)} className="flex h-7 items-center gap-1 rounded-md border border-border px-2 text-[11px] font-medium transition-all hover:bg-accent active:scale-95">
                          <FolderOpen className="h-3.5 w-3.5" />
                          Tải về / Lưu vào…
                        </button>
                      )}
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {/* ── GIỌNG ── */}
            {sub === "voices" && (
              <motion.div key="voices" {...sectionAnim("tb-voices")} className="space-y-3">
                <div className="space-y-2.5 rounded-xl border border-border bg-card p-3">
                  <p className="text-[12px] font-medium">Mẫu giọng của bạn</p>
                  <AudioWorkspace targets={targets} onDone={refresh} />
                  <p
                    className="rounded-lg border border-dashed border-border p-2 text-[11px] text-muted-foreground opacity-70"
                    data-tip="Tool clone giọng (T-06) chưa được làm"
                  >
                    Clone giọng mới từ mẫu: chưa có tool. Hiện chỉ lưu mẫu và phiên âm; clone sẽ thêm khi tool T-06 xong.
                  </p>
                </div>
                <p className="px-0.5 text-[11px] font-medium text-muted-foreground">Giọng trong kho ({vaults.voices.length})</p>
                {vaults.voices.map((v) => {
                  const m = v.metadata || {};
                  const sample = v.files?.samples?.[0];
                  const samplePath = sample && targets ? `${targets.sharedDir}\\voice_vault\\${v.id}\\${sample}` : null;
                  const ready = m.status === "ready";
                  return (
                    <div key={v.id} className={cn("space-y-1.5 rounded-xl border border-border bg-card p-2.5", !ready && "opacity-70")}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="min-w-0">
                          <span className="text-[12px] font-medium">{m.display_name || v.id}</span>{" "}
                          <span className="font-mono text-[10px] text-muted-foreground">({v.id})</span>
                        </span>
                        <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium", ready ? "bg-semantic-success/10 text-semantic-success" : "bg-semantic-warning/10 text-semantic-warning")}>
                          {ready ? "sẵn sàng" : m.status === "todo_clone" ? "chờ clone" : m.status}
                        </span>
                      </div>
                      {m.aliases?.length > 0 && <p className="text-[10px] text-muted-foreground">Tên khác: {m.aliases.join(", ")}</p>}
                      {samplePath && ready && <audio controls src={previewUrl(samplePath)} className="h-8 w-full" />}
                      {saveFor === `v${v.id}` && samplePath ? (
                        <SaveBar targets={targets} files={[{ label: "Mẫu giọng", path: samplePath }]} />
                      ) : (
                        samplePath &&
                        ready && (
                          <button type="button" onClick={() => setSaveFor(`v${v.id}`)} className="flex h-7 items-center gap-1 rounded-md border border-border px-2 text-[11px] font-medium transition-all hover:bg-accent active:scale-95">
                            <FolderOpen className="h-3.5 w-3.5" />
                            Tải về / Lưu vào…
                          </button>
                        )
                      )}
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
