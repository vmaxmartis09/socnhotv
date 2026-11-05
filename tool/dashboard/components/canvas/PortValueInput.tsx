"use client";

import React, { useRef, useState } from "react";
import { useStudioStore } from "@/store";
import {
  fetchProjectLibrary,
  resolveNodeFileUrl,
  uploadNodeFile,
  type LibraryItem,
  type LibraryKind,
} from "@/lib/api/nodes";
import type { PortDefinition } from "@/lib/core-contracts";
import { FolderOpen, Upload, X, Images, Volume2, Film } from "@/components/ui/icons";
import { Reveal } from "./Reveal";
import { cn } from "@/lib/utils";

const MEDIA_KIND: Record<string, LibraryKind | undefined> = {
  image: "image",
  "image[]": "image",
  video: "video",
  audio: "audio",
};

const ACCEPT: Record<LibraryKind, string> = {
  image: "image/png,image/jpeg,image/webp",
  video: "video/mp4,video/webm,video/quicktime",
  audio: "audio/mpeg,audio/wav",
};

const KIND_ICON = { image: Images, video: Film, audio: Volume2 } as const;

/** Cổng có thể nhập tay (text hoặc tệp media). Các kiểu khác chỉ nhận từ dây nối. */
export function canTypeIn(portType: string): boolean {
  return portType === "text" || Boolean(MEDIA_KIND[portType]);
}

interface Props {
  nodeId: string;
  port: PortDefinition;
  value: any;
  /** Cổng đang được nối dây từ node khác */
  connected?: boolean;
}

/**
 * Nhập giá trị cho một cổng vào ngoài việc nối dây:
 * text → ô nhập tự giãn; ảnh/video/âm thanh → tải lên hoặc chọn từ kho dự án.
 */
export function PortValueInput({ nodeId, port, value, connected }: Props) {
  const { activeProjectId, updateNodeParams } = useStudioStore();
  const kind = MEDIA_KIND[port.portType];
  const multi = port.portType === "image[]";
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [picking, setPicking] = useState(false);
  const [items, setItems] = useState<LibraryItem[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (connected) {
    return (
      <div className="rounded-md border border-dashed border-border bg-muted/30 px-2 py-1.5 text-[12px] text-muted-foreground">
        Nhận từ node nối vào
      </div>
    );
  }

  const set = (v: any) => updateNodeParams(nodeId, { [port.name]: v });

  // ----- TEXT -----
  if (port.portType === "text") {
    return (
      <textarea
        rows={2}
        value={typeof value === "string" ? value : ""}
        onChange={(e) => set(e.target.value)}
        placeholder={port.defaultValue ? String(port.defaultValue) : port.description || "Nhập nội dung…"}
        className="nodrag nowheel w-full resize-y rounded-md border border-border bg-card p-2 text-xs leading-relaxed text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-brand"
      />
    );
  }

  if (!kind) return null;

  // ----- MEDIA -----
  const values: string[] = Array.isArray(value) ? value : value ? [value] : [];
  const Icon = KIND_ICON[kind];

  const add = (uri: string) => {
    if (!uri) return;
    if (multi) set([...values.filter((v) => v !== uri), uri]);
    else {
      set(uri);
      setPicking(false);
    }
  };
  const removeAt = (uri: string) => {
    const next = values.filter((v) => v !== uri);
    set(multi ? next : "");
  };

  const openPicker = async () => {
    const open = !picking;
    setPicking(open);
    if (open && items === null) setItems(await fetchProjectLibrary(activeProjectId, kind));
  };

  const onFile = async (file: File) => {
    setErr(null);
    setBusy(true);
    try {
      const res = await uploadNodeFile(activeProjectId, file);
      add(res.uri);
      setItems(null); // làm mới kho ở lần mở sau
    } catch (e: any) {
      setErr(e?.message || "Tải lên thất bại");
    } finally {
      setBusy(false);
    }
  };

  const preview = (uri: string) => {
    const url = resolveNodeFileUrl(activeProjectId, uri);
    const name = uri.split("/").pop() || uri;
    return (
      <div key={uri} className="group relative flex items-center gap-2 rounded-md border border-border bg-card p-1">
        {kind === "image" && url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={name} className="h-10 w-10 shrink-0 rounded object-cover object-top" />
        ) : (
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-muted text-muted-foreground">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <span className="min-w-0 flex-1 truncate text-[12px] text-foreground" title={name}>
          {name}
        </span>
        {kind === "audio" && url && <audio src={url} controls preload="none" className="nodrag h-6 w-24 shrink-0" />}
        <button
          type="button"
          onClick={() => removeAt(uri)}
          title="Bỏ"
          className="nodrag flex h-6 w-6 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  };

  return (
    <div className="space-y-1.5">
      <input
        ref={fileRef}
        type="file"
        accept={ACCEPT[kind]}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
      {values.map(preview)}

      {(multi || values.length === 0) && (
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            disabled={busy}
            onClick={() => fileRef.current?.click()}
            className="nodrag flex h-8 flex-1 items-center justify-center gap-1.5 rounded-md border border-border bg-card text-xs text-foreground transition-colors hover:bg-accent disabled:opacity-60"
          >
            <Upload className="h-3.5 w-3.5" />
            {busy ? "Đang tải…" : "Tải lên"}
          </button>
          <button
            type="button"
            onClick={openPicker}
            className={cn(
              "nodrag flex h-8 flex-1 items-center justify-center gap-1.5 rounded-md border text-xs text-foreground transition-colors hover:bg-accent",
              picking ? "border-foreground bg-accent" : "border-border bg-card"
            )}
          >
            <FolderOpen className="h-3.5 w-3.5" />
            Từ dự án
          </button>
        </div>
      )}

      <Reveal show={picking}>
        <div className="rounded-md border border-border bg-muted/20 p-1.5">
          {items === null ? (
            <p className="p-2 text-center text-[12px] text-muted-foreground">Đang tải…</p>
          ) : items.length === 0 ? (
            <p className="p-2 text-center text-[12px] text-muted-foreground">Dự án chưa có tệp loại này.</p>
          ) : (
            <div className="nowheel grid max-h-44 grid-cols-3 gap-1.5 overflow-y-auto">
              {items.map((it) => {
                const picked = values.includes(it.uri || "");
                return (
                  <button
                    key={it.uri || it.url}
                    type="button"
                    onClick={() => add(it.uri || "")}
                    title={it.name}
                    className={cn(
                      "nodrag relative aspect-square overflow-hidden rounded border bg-card text-muted-foreground transition-colors hover:border-foreground",
                      picked ? "border-foreground" : "border-border"
                    )}
                  >
                    {kind === "image" ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={it.url} alt={it.name} loading="lazy" className="h-full w-full object-cover object-top" />
                    ) : (
                      <span className="flex h-full w-full flex-col items-center justify-center gap-1 p-1">
                        <Icon className="h-4 w-4" />
                        <span className="w-full truncate text-center text-[10px]">{it.name}</span>
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </Reveal>

      {err && <p className="text-[12px] text-destructive">{err}</p>}
    </div>
  );
}
