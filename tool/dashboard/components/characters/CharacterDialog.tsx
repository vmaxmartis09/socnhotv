"use client";

import React, { useRef, useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import type { Character } from "@/lib/repositories";
import { toDataUrl } from "@/lib/repositories/character-assets";
import { VoiceSelectorWithClone } from "@/components/voice/VoiceSelectorWithClone";
import { Button } from "@/components/ui/Button";
import { X, Check, Upload, Images, Trash2, Sparkles, Plus, Loader2 } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);

const inputCls =
  "w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1 text-[13px] font-medium text-muted-foreground">
      <span>{label}</span>
      {children}
    </label>
  );
}

interface ImageItem {
  id: string;
  url: string;
  name: string;
  file?: File;
  isExisting?: boolean;
}

interface Props {
  /** Có `initial` => sửa; không có => tạo mới. */
  initial?: Character;
  /** Điền sẵn khi tạo mới (ví dụ bản nháp do AI dựng) */
  prefill?: Partial<Character>;
  /** Hiển thị trong vùng mở rộng của panel (không có lớp phủ modal) */
  inline?: boolean;
  projectId: string;
  onSave: (
    c: Character,
    isNew: boolean,
    pendingFiles?: File[],
    removedImageNames?: string[]
  ) => Promise<void>;
  onClose: () => void;
}

export function CharacterDialog({ initial, prefill, projectId, onSave, onClose, inline = false }: Props) {
  const base = initial ?? prefill;
  const t = useTranslations("characters");
  const isNew = !initial;

  const [id, setId] = useState(initial?.id ?? prefill?.id ?? "");
  const [idTouched, setIdTouched] = useState(Boolean(initial?.id || prefill?.id));
  const [name, setName] = useState(base?.name ?? "");
  const [role, setRole] = useState<Character["role"]>(base?.role ?? "supporting");
  const [heightCm, setHeightCm] = useState(String(base?.heightCm ?? 100));
  const [scaleRatio, setScaleRatio] = useState(String(base?.scaleRatio ?? 1));
  const [description, setDescription] = useState(base?.description ?? "");
  const [tempo, setTempo] = useState(String(initial?.defaultTempo ?? 1));
  const [voiceId, setVoiceId] = useState(base?.voiceId ?? "");
  const [promptLock, setPromptLock] = useState(base?.promptLock ?? "");
  const [personality, setPersonality] = useState(base?.memory?.personality ?? "");
  const [catchphrases, setCatchphrases] = useState((base?.memory?.catchphrases ?? []).join("\n"));
  const [habits, setHabits] = useState((base?.memory?.habits ?? []).join("\n"));
  const [events, setEvents] = useState((base?.memory?.pastEventsSummary ?? []).join("\n"));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Quản lý ảnh DNA nhân vật
  const [images, setImages] = useState<ImageItem[]>(() => {
    const rawList = initial?.referenceImages ?? [];
    return rawList.map((url, idx) => ({
      id: `existing_${idx}_${url}`,
      url,
      name: decodeURIComponent(url.split("/").pop() ?? `dna_${idx + 1}.png`),
      isExisting: true,
    }));
  });

  const [primaryId, setPrimaryId] = useState<string>(() => {
    const rawList = initial?.referenceImages ?? [];
    if (initial?.primaryImage) {
      const pIdx = rawList.findIndex((u) => decodeURIComponent(u.split("/").pop() ?? "") === initial.primaryImage);
      if (pIdx >= 0) return `existing_${pIdx}_${rawList[pIdx]}`;
    }
    return rawList.length > 0 ? `existing_0_${rawList[0]}` : "";
  });

  const [removedExistingNames, setRemovedExistingNames] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tự sinh id dạng slug khi người dùng nhập tên (nếu chưa gõ id thủ công)
  const handleNameChange = (val: string) => {
    setName(val);
    if (isNew && !idTouched) {
      const slug = val
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
      setId(slug);
    }
  };

  const handleFiles = (fileList: File[]) => {
    const validFiles = fileList.filter((f) =>
      ["image/png", "image/jpeg", "image/jpg", "image/webp"].includes(f.type.toLowerCase()) ||
      /\.(png|jpe?g|webp)$/i.test(f.name)
    );
    if (validFiles.length === 0) return;

    const newItems: ImageItem[] = validFiles.map((file, i) => ({
      id: `file_${Date.now()}_${i}_${file.name}`,
      url: URL.createObjectURL(file),
      name: file.name,
      file,
      isExisting: false,
    }));

    setImages((prev) => {
      const next = [...prev, ...newItems];
      if (!primaryId && next.length > 0) {
        setPrimaryId(next[0].id);
      }
      return next;
    });
  };

  const removeImage = (idToRemove: string) => {
    setImages((prev) => {
      const item = prev.find((x) => x.id === idToRemove);
      if (item?.isExisting) {
        setRemovedExistingNames((r) => [...r, item.name]);
      } else if (item?.url.startsWith("blob:")) {
        URL.revokeObjectURL(item.url);
      }
      const next = prev.filter((x) => x.id !== idToRemove);
      if (primaryId === idToRemove) {
        setPrimaryId(next[0]?.id ?? "");
      }
      return next;
    });
  };

  // Dọn dẹp blob URLs khi unmount
  useEffect(() => {
    return () => {
      images.forEach((img) => {
        if (!img.isExisting && img.url.startsWith("blob:")) {
          URL.revokeObjectURL(img.url);
        }
      });
    };
  }, [images]);

  const idValid = /^[A-Za-z0-9_-]+$/.test(id);
  const canSave = name.trim() !== "" && (!isNew || idValid) && !busy;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSave) return;
    setBusy(true);
    setError("");

    try {
      // 1. Sắp xếp danh sách sao cho ảnh chính (primary) nằm ở vị trí đầu tiên
      const sortedImages = [...images];
      const primaryIdx = sortedImages.findIndex((x) => x.id === primaryId);
      if (primaryIdx > 0) {
        const [primaryItem] = sortedImages.splice(primaryIdx, 1);
        sortedImages.unshift(primaryItem);
      }

      // 2. Chuyển đổi ảnh mới sang base64 Data URL để lưu offline/local ngay lập tức
      const pendingFiles: File[] = [];
      const finalRefImages: string[] = [];

      for (const item of sortedImages) {
        if (item.file) {
          pendingFiles.push(item.file);
          try {
            const dataUrl = await toDataUrl(item.file);
            finalRefImages.push(dataUrl);
          } catch {
            finalRefImages.push(item.url);
          }
        } else {
          finalRefImages.push(item.url);
        }
      }

      const primaryName = sortedImages[0]?.name;

      await onSave(
        {
          id: initial?.id ?? id,
          projectId,
          name: name.trim(),
          role,
          heightCm: Number(heightCm) || 0,
          scaleRatio: Number(scaleRatio) || 1,
          voiceId: voiceId.trim(),
          description,
          defaultTempo: Number(tempo) || 1,
          promptLock,
          primaryImage: primaryName,
          referenceImages: finalRefImages,
          memory: {
            personality,
            catchphrases: lines(catchphrases),
            habits: lines(habits),
            pastEventsSummary: lines(events),
          },
        },
        isNew,
        pendingFiles,
        removedExistingNames
      );
      onClose();
    } catch (err) {
      setError(t("error", { message: err instanceof Error ? err.message : String(err) }));
      setBusy(false);
    }
  }

  const formEl = (
    <form
      role={inline ? undefined : "dialog"}
      aria-modal={inline ? undefined : true}
      aria-label={isNew ? t("createTitle") : t("editTitle")}
      onSubmit={submit}
      className={
        inline
          ? "space-y-4"
          : "max-h-full w-full max-w-xl space-y-4 overflow-y-auto scroll-quiet rounded-lg border border-border bg-card p-5"
      }
    >
      {!inline && (
        <h2 className="text-base font-semibold text-foreground">
          {isNew ? t("createTitle") : t("editTitle")}
        </h2>
      )}

      {/* Thông số cơ bản */}
      <div className={inline ? "grid grid-cols-2 gap-3" : "grid grid-cols-1 gap-3 sm:grid-cols-2"}>
        <Field label={t("fId")}>
          <input
            className={inputCls}
            value={id}
            disabled={!isNew}
            onChange={(e) => {
              setIdTouched(true);
              setId(e.target.value);
            }}
            placeholder="soc_nho"
          />
        </Field>
        <Field label={t("fName")}>
          <input className={inputCls} value={name} onChange={(e) => handleNameChange(e.target.value)} />
        </Field>
        <Field label={t("fRole")}>
          <select className={inputCls} value={role} onChange={(e) => setRole(e.target.value as Character["role"])}>
            <option value="main">{t("roleMain")}</option>
            <option value="supporting">{t("roleSupporting")}</option>
          </select>
        </Field>
        <div className="space-y-1">
          <span className="block text-[13px] font-medium text-muted-foreground">
            {t("fVoice")}
          </span>
          <VoiceSelectorWithClone
            value={voiceId}
            onChange={(newVid) => setVoiceId(newVid)}
            projectId={projectId}
            characterId={initial?.id ?? id}
            characterName={name}
          />
        </div>
        <Field label={t("fHeight")}>
          <input className={inputCls} type="number" min={1} value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
        </Field>
        <Field label={t("fScale")}>
          <input className={inputCls} type="number" step="0.1" min={0.1} value={scaleRatio} onChange={(e) => setScaleRatio(e.target.value)} />
        </Field>
      </div>

      <Field label={t("fTempo")}>
        <input className={inputCls} type="number" step="0.05" min={0.5} max={2} value={tempo} onChange={(e) => setTempo(e.target.value)} />
      </Field>

      {/* KHU VỰC TẢI LÊN ẢNH DNA NHÂN VẬT (MASTER DNA REFERENCE IMAGES) */}
      <div className="space-y-2 rounded-xl border border-border bg-muted/20 p-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Images className="h-4 w-4 text-brand" />
            <span className="text-[13px] font-semibold text-foreground">
              {t("dnaImagesTitle")}
            </span>
            {images.length > 0 && (
              <span className="rounded-full bg-brand/10 px-2 py-0.5 text-[11px] font-medium text-brand tnum">
                {images.length}
              </span>
            )}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 gap-1.5 text-xs"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-3.5 w-3.5" />
            <span>{t("uploadImages")}</span>
          </Button>
        </div>

        <p className="text-xs leading-relaxed text-muted-foreground">
          {t("dnaImagesHint")}
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          hidden
          onChange={(e) => {
            const files = Array.from(e.target.files ?? []);
            e.target.value = "";
            if (files.length) handleFiles(files);
          }}
        />

        {images.length === 0 ? (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const droppedFiles = Array.from(e.dataTransfer.files);
              if (droppedFiles.length) handleFiles(droppedFiles);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-5 text-center cursor-pointer transition-colors",
              isDragging
                ? "border-brand bg-brand/5 ring-2 ring-brand"
                : "border-border hover:border-foreground/40 hover:bg-muted/40"
            )}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent">
              <Upload className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-foreground">
                {t("dropImagesHere")}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Khuyến nghị: 2 - 4 góc ảnh (chính diện, góc nghiêng 3/4, toàn thân).
              </p>
            </div>
          </div>
        ) : (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const droppedFiles = Array.from(e.dataTransfer.files);
              if (droppedFiles.length) handleFiles(droppedFiles);
            }}
            className={cn(
              "grid grid-cols-2 gap-2.5 sm:grid-cols-4 rounded-xl p-1 transition-all",
              isDragging && "ring-2 ring-brand bg-brand/5"
            )}
          >
            {images.map((item) => {
              const isPrimary = item.id === primaryId;
              return (
                <div
                  key={item.id}
                  className={cn(
                    "group relative aspect-[3/4] overflow-hidden rounded-xl border bg-card transition-all",
                    isPrimary ? "border-brand ring-2 ring-brand shadow-sm" : "border-border"
                  )}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img decoding="async" loading="lazy"
                    src={item.url}
                    alt={item.name}
                    className="h-full w-full object-cover object-top transition-transform duration-300 group-hover:scale-105"
                  />

                  {/* Huy hiệu ảnh chính */}
                  {isPrimary && (
                    <span className="absolute left-1.5 top-1.5 z-10 flex items-center gap-1 rounded-full bg-brand px-1.5 py-0.5 text-[10px] font-medium text-white shadow-sm">
                      <Sparkles className="h-2.5 w-2.5" />
                      {t("primary")}
                    </span>
                  )}

                  {/* Lớp phủ thao tác khi rê chuột */}
                  <div className="absolute inset-0 flex items-center justify-center gap-1.5 bg-black/50 opacity-0 backdrop-blur-[2px] transition-opacity group-hover:opacity-100">
                    {!isPrimary && (
                      <button
                        type="button"
                        title={t("setPrimary")}
                        aria-label={t("setPrimary")}
                        onClick={(e) => {
                          e.stopPropagation();
                          setPrimaryId(item.id);
                        }}
                        className="flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-foreground hover:bg-card hover:scale-110 active:scale-90"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      type="button"
                      title={t("removeImage")}
                      aria-label={t("removeImage")}
                      onClick={(e) => {
                        e.stopPropagation();
                        removeImage(item.id);
                      }}
                      className="flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-semantic-danger hover:bg-card hover:scale-110 active:scale-90"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  {/* Tên tệp dưới chân ảnh */}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent p-1.5 pt-4">
                    <p className="truncate text-[10px] text-white/95" title={item.name}>
                      {item.name}
                    </p>
                  </div>
                </div>
              );
            })}

            {/* Ô bấm thêm ảnh */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex aspect-[3/4] flex-col items-center justify-center gap-1.5 rounded-xl border-2 border-dashed border-border bg-card/40 text-muted-foreground transition-all hover:border-foreground/40 hover:text-foreground active:scale-95"
            >
              <Plus className="h-5 w-5" />
              <span className="text-[11px] font-medium">{t("uploadImages")}</span>
            </button>
          </div>
        )}
      </div>

      <Field label={t("fDescription")}>
        <textarea className={inputCls} rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </Field>
      <Field label={t("fPrompt")}>
        <textarea className={inputCls} rows={3} value={promptLock} onChange={(e) => setPromptLock(e.target.value)} />
      </Field>
      <Field label={t("fPersonality")}>
        <input className={inputCls} value={personality} onChange={(e) => setPersonality(e.target.value)} />
      </Field>
      <div className={inline ? "grid grid-cols-1 gap-3" : "grid grid-cols-1 gap-3 sm:grid-cols-3"}>
        <Field label={t("fCatch")}>
          <textarea className={inputCls} rows={3} value={catchphrases} onChange={(e) => setCatchphrases(e.target.value)} />
        </Field>
        <Field label={t("fHabits")}>
          <textarea className={inputCls} rows={3} value={habits} onChange={(e) => setHabits(e.target.value)} />
        </Field>
        <Field label={t("fEvents")}>
          <textarea className={inputCls} rows={3} value={events} onChange={(e) => setEvents(e.target.value)} />
        </Field>
      </div>

      {error && <p className="text-[13px] text-semantic-danger">{error}</p>}

      <div className="flex items-center justify-between pt-1">
        {busy ? (
          <span className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-brand" />
            {t("savingWithImages")}
          </span>
        ) : (
          <span />
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" size="icon" title={t("cancel")} aria-label={t("cancel")} disabled={busy} onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
          <Button type="submit" size="icon" title={t("save")} aria-label={t("save")} disabled={!canSave}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </form>
  );

  if (inline) return formEl;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      {formEl}
    </div>
  );
}
