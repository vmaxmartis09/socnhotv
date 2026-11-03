"use client";

import React, { useState } from "react";
import { generateScriptDraft, saveScript, type LibraryEpisode } from "@/lib/repositories/library";
import { AiLoading } from "@/components/ui/AiLoading";
import { Wand2, Check } from "@/components/ui/icons";
import { Markdown } from "./Markdown";
import { cn } from "@/lib/utils";

const inputCls = "w-full rounded-xl border border-border bg-card px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** Soạn kịch bản Markdown: tự viết hoặc nhờ AI dựng từ ý tưởng, rồi lưu vào một tập. Hiển thị trong vùng mở rộng. */
export function ScriptComposer({
  projectId,
  episodes,
  mockMode,
  startWithAi,
  onSaved,
  onClose,
}: {
  projectId: string;
  episodes: LibraryEpisode[];
  mockMode: boolean;
  startWithAi?: boolean;
  onSaved: () => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [episodeId, setEpisodeId] = useState("");
  const [idea, setIdea] = useState("");
  const [md, setMd] = useState("");
  const [preview, setPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    if (!idea.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      const { markdown } = await generateScriptDraft(projectId, idea, mockMode);
      setMd(markdown);
      if (!title.trim()) {
        const h = markdown.match(/^#\s+(.+)$/m);
        if (h) setTitle(h[1].trim());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!title.trim() || saving) return;
    setSaving(true);
    setError("");
    try {
      await saveScript(projectId, title.trim(), md, episodeId || undefined);
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      <input className={inputCls} placeholder="Tiêu đề kịch bản" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus={!startWithAi} />
      <select className={inputCls} value={episodeId} onChange={(e) => setEpisodeId(e.target.value)} aria-label="Lưu vào tập">
        <option value="">Tập mới (đặt theo tiêu đề)</option>
        {episodes.map((e) => (
          <option key={e.id} value={e.id}>{e.title}</option>
        ))}
      </select>

      <div className="space-y-2 rounded-2xl border border-border bg-gradient-to-br from-brand/5 to-transparent p-3">
        <div className="flex items-center gap-2 text-[13px] font-medium">
          <Wand2 className="h-4 w-4 text-brand" />
          <span>Nhờ AI viết nháp từ ý tưởng</span>
        </div>
        <textarea
          className={inputCls}
          rows={3}
          placeholder="Ví dụ: Bi sâu răng vì ăn kẹo, bác sĩ Koala hướng dẫn đánh răng đúng cách"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          autoFocus={startWithAi}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) generate(); }}
        />
        {busy ? (
          <AiLoading label="AI đang viết kịch bản…" lines={3} />
        ) : (
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-muted-foreground">{mockMode ? "Chế độ thử: mẫu có sẵn ($0)" : "Gemini (có phí)"} · Ctrl+Enter</span>
            <button type="button" title="Viết bằng AI" aria-label="Viết bằng AI" onClick={generate} disabled={!idea.trim()} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90 disabled:opacity-40">
              <Wand2 className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 text-xs">
        {[false, true].map((p) => (
          <button key={String(p)} type="button" onClick={() => setPreview(p)} className={cn("rounded-full border px-2.5 py-1", preview === p ? "border-foreground bg-accent" : "border-border text-muted-foreground")}>
            {p ? "Xem trước" : "Soạn"}
          </button>
        ))}
      </div>
      {preview ? (
        <div className="min-h-[200px] rounded-xl border border-border bg-card p-4"><Markdown>{md || "…"}</Markdown></div>
      ) : (
        <textarea className={cn(inputCls, "min-h-[240px] font-mono text-xs leading-relaxed")} placeholder="# Tiêu đề&#10;&#10;Nội dung Markdown…" value={md} onChange={(e) => setMd(e.target.value)} />
      )}

      {error && <p className="text-xs text-semantic-danger">{error}</p>}
      <div className="flex justify-end">
        <button type="button" title="Lưu kịch bản" aria-label="Lưu kịch bản" onClick={save} disabled={!title.trim() || saving} className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90 disabled:opacity-40">
          <Check className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
