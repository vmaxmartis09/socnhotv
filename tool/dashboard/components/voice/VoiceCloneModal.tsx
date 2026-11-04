"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  X,
  Upload,
  Mic,
  Sparkles,
  Loader2,
  Check,
  Play,
  Pause,
  AlertTriangle,
  AudioLines,
} from "@/components/ui/icons";
import {
  cloneCharacterVoice,
  type VoiceCloneResult,
} from "@/lib/repositories/character-assets";
import { CORE_URL } from "@/lib/repositories/core";
import { cn } from "@/lib/utils";

export interface VoiceCloneModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultVoiceId?: string;
  defaultDialect?: "south" | "north" | "central";
  projectId?: string;
  characterId?: string;
  sourceSamples?: Array<{ name: string; url: string }>;
  onSuccess?: (result: VoiceCloneResult) => void;
}

export function VoiceCloneModal({
  isOpen,
  onClose,
  defaultVoiceId = "",
  defaultDialect = "south",
  projectId,
  characterId,
  sourceSamples = [],
  onSuccess,
}: VoiceCloneModalProps) {
  const [voiceId, setVoiceId] = useState(defaultVoiceId || "custom-voice");
  const [dialect, setDialect] = useState<"south" | "north" | "central">(defaultDialect);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedExistingSample, setSelectedExistingSample] = useState<string>("");
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progressText, setProgressText] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<VoiceCloneResult | null>(null);

  // Audio preview state for cloned result
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (defaultVoiceId) {
      setVoiceId(defaultVoiceId);
    }
  }, [defaultVoiceId]);

  useEffect(() => {
    if (!isOpen) {
      setError("");
      setResult(null);
      setBusy(false);
      setIsPlaying(false);
      if (audioRef.current) {
        audioRef.current.pause();
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSlugify = (val: string) => {
    const slug = val
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9_-]+/g, "-")
      .replace(/^-+|-+$/g, "");
    setVoiceId(slug);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setSelectedExistingSample("");
      if (!defaultVoiceId) {
        const base = file.name.replace(/\.[^/.]+$/, "");
        handleSlugify(base);
      }
    }
  };

  const handleStartClone = async () => {
    if (!consentConfirmed) {
      setError("Bạn cần xác nhận quyền sở hữu hoặc sự đồng ý đối với mẫu giọng nói.");
      return;
    }
    if (!selectedFile && !selectedExistingSample) {
      setError("Vui lòng tải lên tệp âm thanh/video hoặc chọn một mẫu giọng có sẵn.");
      return;
    }
    const cleanId = voiceId.trim();
    if (!cleanId || cleanId.length < 2) {
      setError("Mã giọng không hợp lệ (tối thiểu 2 ký tự).");
      return;
    }

    setBusy(true);
    setError("");
    setProgressText("Đang xử lý âm thanh & lọc tạp âm...");

    const t1 = setTimeout(() => {
      setProgressText("Faster-Whisper đang tự động trích xuất transcript...");
    }, 2000);

    const t2 = setTimeout(() => {
      setProgressText("OmniVoice đang phân tích embedding vector & TikTok mastering (-14 LUFS)...");
    }, 5500);

    try {
      const res = await cloneCharacterVoice({
        voiceId: cleanId,
        projectId,
        characterId,
        file: selectedFile || undefined,
        sourceFile: selectedExistingSample || undefined,
        dialect,
        consentConfirmed: true,
      });

      clearTimeout(t1);
      clearTimeout(t2);
      setResult(res);
      if (onSuccess) {
        onSuccess(res);
      }
    } catch (err: any) {
      clearTimeout(t1);
      clearTimeout(t2);
      setError(err.message || "Quá trình nhân bản giọng thất bại. Hãy kiểm tra lại tệp nguồn.");
    } finally {
      setBusy(false);
      setProgressText("");
    }
  };

  const togglePlaySample = () => {
    if (!result?.sampleUrl) return;
    if (!audioRef.current) {
      const fullUrl = result.sampleUrl.startsWith("http")
        ? result.sampleUrl
        : `${CORE_URL}${result.sampleUrl}`;
      audioRef.current = new Audio(fullUrl);
      audioRef.current.onended = () => setIsPlaying(false);
    }
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <Mic className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground flex items-center gap-1.5">
                <span>Nhân bản giọng nói OmniVoice</span>
                <Sparkles className="h-4 w-4 text-brand" />
              </h3>
              <p className="text-xs text-muted-foreground">
                Tạo giọng nói AI từ mẫu giọng thực tế (-14 LUFS chuẩn TikTok)
              </p>
            </div>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Cảnh báo bản quyền & điều khoản pháp lý */}
        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-600 dark:text-amber-400">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            Bạn chỉ được nhân bản giọng nói của chính bạn hoặc của người đã cho phép. Tuyệt đối không giả mạo giọng nói khi chưa có sự đồng ý.
          </p>
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-semantic-danger/40 bg-semantic-danger/10 p-3 text-xs text-semantic-danger">
            {error}
          </div>
        )}

        {/* Nội dung khi chưa xong */}
        {!result ? (
          <div className="mt-4 space-y-4">
            {/* Chọn nguồn âm thanh */}
            <div>
              <span className="text-xs font-medium text-foreground block mb-1.5">
                Tệp âm thanh / video mẫu (3 - 10 giây)
              </span>

              {sourceSamples.length > 0 && (
                <div className="mb-2">
                  <span className="text-[11px] text-muted-foreground block mb-1">
                    Chọn từ mẫu có sẵn của nhân vật:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {sourceSamples.map((s) => (
                      <button
                        key={s.name}
                        type="button"
                        onClick={() => {
                          setSelectedExistingSample(s.name);
                          setSelectedFile(null);
                        }}
                        className={cn(
                          "rounded-md border px-2.5 py-1 text-xs transition-colors",
                          selectedExistingSample === s.name
                            ? "border-brand bg-brand/10 text-brand font-medium"
                            : "border-border text-muted-foreground hover:bg-accent"
                        )}
                      >
                        {s.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Box kéo thả hoặc upload */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-4 text-center cursor-pointer transition-colors",
                  selectedFile
                    ? "border-brand bg-brand/5"
                    : "border-border hover:border-foreground/40 hover:bg-muted/30"
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,video/mp4,video/quicktime,video/webm"
                  hidden
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setSelectedFile(f);
                      setSelectedExistingSample("");
                      if (!defaultVoiceId) {
                        const base = f.name.replace(/\.[^/.]+$/, "");
                        handleSlugify(base);
                      }
                    }
                  }}
                />
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-foreground">
                  <Upload className="h-4 w-4" />
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-xs font-semibold text-brand flex items-center justify-center gap-1">
                      <Check className="h-3.5 w-3.5" />
                      <span>{selectedFile.name}</span>
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Nhấp để đổi tệp khác
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-xs font-medium text-foreground">
                      Kéo thả hoặc nhấn để chọn tệp âm thanh/video
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Hỗ trợ: .mp3, .wav, .m4a, .mp4, .mov (tối ưu nhất: 4 - 8 giây giọng nói rõ ràng)
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Cấu hình mã giọng & phương ngữ */}
            <div className="grid grid-cols-2 gap-3">
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Mã giọng (Voice ID)</span>
                <input
                  type="text"
                  disabled={busy}
                  value={voiceId}
                  onChange={(e) => handleSlugify(e.target.value)}
                  placeholder="vi-du-be-an"
                  className="h-8 w-full rounded-lg border border-border bg-background px-2.5 font-mono text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </label>

              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Phương ngữ giọng</span>
                <select
                  disabled={busy}
                  value={dialect}
                  onChange={(e) => setDialect(e.target.value as any)}
                  className="h-8 w-full rounded-lg border border-border bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                >
                  <option value="south">Miền Nam</option>
                  <option value="north">Miền Bắc</option>
                  <option value="central">Miền Trung</option>
                </select>
              </label>
            </div>

            {/* Checkbox cam kết */}
            <label className="flex items-start gap-2.5 pt-1 cursor-pointer">
              <input
                type="checkbox"
                disabled={busy}
                checked={consentConfirmed}
                onChange={(e) => setConsentConfirmed(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-border text-brand focus:ring-brand"
              />
              <span className="text-xs text-muted-foreground leading-normal">
                Tôi cam kết đây là giọng nói của chính tôi hoặc tôi đã có văn bản ủy quyền / cho phép sử dụng từ chủ sở hữu.
              </span>
            </label>

            {/* Loading status */}
            {busy && (
              <div className="rounded-xl border border-brand/30 bg-brand/5 p-3 flex items-center gap-3 animate-pulse">
                <Loader2 className="h-4 w-4 text-brand animate-spin shrink-0" />
                <span className="text-xs text-brand font-medium">
                  {progressText || "Đang tiến hành nhân bản giọng nói..."}
                </span>
              </div>
            )}

            {/* Footer action */}
            <div className="flex justify-end gap-2.5 pt-2 border-t border-border">
              <button
                type="button"
                disabled={busy}
                onClick={onClose}
                className="h-8.5 rounded-lg border border-border px-3.5 text-xs font-medium text-foreground hover:bg-accent disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                type="button"
                disabled={!consentConfirmed || (!selectedFile && !selectedExistingSample) || busy}
                onClick={handleStartClone}
                className="flex h-8.5 items-center gap-1.5 rounded-lg bg-brand px-4 text-xs font-medium text-brand-foreground shadow hover:opacity-90 disabled:opacity-40 transition-all"
              >
                {busy ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Đang nhân bản...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Bắt đầu nhân bản giọng</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Kết quả thành công */
          <div className="mt-4 space-y-4 animate-in zoom-in-95 duration-200">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-3">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm">
                <Check className="h-4 w-4" />
                <span>Nhân bản giọng thành công!</span>
              </div>

              <div className="space-y-1.5 text-xs text-foreground">
                <p>
                  <span className="text-muted-foreground">Mã giọng:</span>{" "}
                  <code className="font-mono font-medium text-brand">{result.voiceId}</code>
                </p>
                <p>
                  <span className="text-muted-foreground">Phương ngữ:</span>{" "}
                  <span className="capitalize">{result.dialect}</span> ·{" "}
                  <span className="text-muted-foreground">Thời lượng:</span>{" "}
                  {result.durationSec ? `${result.durationSec}s` : "chuẩn"}
                </p>
                {result.transcript && (
                  <p className="rounded bg-background/80 p-2 text-[11px] italic text-muted-foreground border border-border">
                    &ldquo;{result.transcript}&rdquo;
                  </p>
                )}
              </div>

              {/* Nút nghe thử */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={togglePlaySample}
                  className="flex h-8 items-center gap-1.5 rounded-lg bg-emerald-600 px-3 text-xs font-medium text-white hover:bg-emerald-700 transition-colors shadow-sm"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="h-3.5 w-3.5" />
                      <span>Dừng</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5" />
                      <span>Nghe thử mẫu giọng đã clone</span>
                    </>
                  )}
                </button>
                <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                  <AudioLines className="h-3.5 w-3.5 text-emerald-500" />
                  <span>{result.mastering}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2.5 pt-2 border-t border-border">
              <button
                type="button"
                onClick={onClose}
                className="flex h-8.5 items-center gap-1.5 rounded-lg bg-primary px-4 text-xs font-medium text-primary-foreground shadow hover:opacity-90"
              >
                <Check className="h-3.5 w-3.5" />
                <span>Hoàn tất & Sử dụng giọng này</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
