"use client";

import React, { useMemo, useRef, useState } from "react";
import type { Edge } from "@xyflow/react";
import { useStudioStore } from "@/store";
import { PORT_TYPE_COLORS } from "@/store/slices/canvasSlice";
import {
  fetchProjectLibrary,
  resolveNodeFileUrl,
  uploadNodeFile,
  type LibraryItem,
  type LibraryKind,
} from "@/lib/api/nodes";
import { FALLBACK_NODE_TYPES, isPortCompatible } from "@/lib/core-api";
import { applyPortOverride } from "@/lib/node-ports";
import type { NodeDefinition, PortDefinition } from "@/lib/core-contracts";
import { FolderOpen, Upload, X, Images, Volume2, Film, Users, Layers, Unlink } from "@/components/ui/icons";
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

type Panel = "node" | "project" | "character" | null;

/** Cổng có thể nhập tay (text hoặc tệp media). */
export function canTypeIn(portType: string): boolean {
  return portType === "text" || Boolean(MEDIA_KIND[portType]);
}

function wouldCreateCycle(edges: Edge[], sourceId: string, targetId: string): boolean {
  if (sourceId === targetId) return true;
  const seen = new Set<string>();
  const stack = [targetId];
  while (stack.length) {
    const cur = stack.pop()!;
    if (cur === sourceId) return true;
    if (seen.has(cur)) continue;
    seen.add(cur);
    for (const e of edges) if (e.source === cur) stack.push(e.target);
  }
  return false;
}

interface CharAttr {
  key: string;
  label: string;
  value: string;
  image?: boolean;
}

interface Props {
  nodeId: string;
  port: PortDefinition;
}

/**
 * Chọn nguồn cho một cổng vào — không chỉ nối dây:
 * output của node khác · tải lên · tệp trong dự án · thuộc tính của nhân vật · gõ trực tiếp (text).
 * Có nút gỡ dây / bỏ giá trị.
 */
export function PortValueInput({ nodeId, port }: Props) {
  const {
    activeProjectId,
    nodes,
    edges,
    nodeCatalog,
    characters,
    updateNodeParams,
    setNodesAndEdges,
  } = useStudioStore() as any;

  const kind = MEDIA_KIND[port.portType];
  const multi = port.portType === "image[]";
  const self = nodes.find((n: any) => n.id === nodeId);
  const value = self?.data?.params?.[port.name];
  const incoming: Edge | undefined = edges.find((e: Edge) => e.target === nodeId && e.targetHandle === port.name);

  const fileRef = useRef<HTMLInputElement | null>(null);
  const [panel, setPanel] = useState<Panel>(null);
  const [items, setItems] = useState<LibraryItem[] | null>(null);
  const [charId, setCharId] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const baseDefOf = (type: string): NodeDefinition | undefined =>
    (nodeCatalog as NodeDefinition[]).find((d) => d.typeName === type) ||
    FALLBACK_NODE_TYPES.find((d) => d.typeName === type);

  const labelOf = (n: any) => {
    const base = baseDefOf(n.data.nodeType);
    return base ? applyPortOverride(base, n.data.params).displayName : n.data.nodeType;
  };

  // ----- Nguồn: output của node khác (tương thích kiểu, không tạo vòng) -----
  const candidates = useMemo(() => {
    const out: { nodeId: string; port: string; type: string; label: string }[] = [];
    const counts = new Map<string, number>();
    for (const n of nodes) {
      if (n.id === nodeId) continue;
      if (wouldCreateCycle(edges, n.id, nodeId)) continue;
      const base = baseDefOf(n.data.nodeType);
      if (!base) continue;
      const def = applyPortOverride(base, n.data.params);
      const title = def.displayName;
      const idx = (counts.get(title) || 0) + 1;
      counts.set(title, idx);
      for (const op of def.outputPorts) {
        if (!isPortCompatible(op.portType, port.portType)) continue;
        out.push({ nodeId: n.id, port: op.name, type: op.portType, label: idx > 1 ? `${title} #${idx}` : title });
      }
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, nodeId, port.portType, nodeCatalog]);

  const connectTo = (c: { nodeId: string; port: string; type: string }) => {
    const color = PORT_TYPE_COLORS[c.type as keyof typeof PORT_TYPE_COLORS] || "#737373";
    const edge: Edge = {
      id: `edge_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`,
      source: c.nodeId,
      sourceHandle: c.port,
      target: nodeId,
      targetHandle: port.name,
      type: "default",
      style: { stroke: color, strokeWidth: 1.75 },
      data: { portType: c.type },
    };
    const rest = edges.filter((e: Edge) => !(e.target === nodeId && e.targetHandle === port.name));
    setNodesAndEdges(nodes, [...rest, edge], true);
    setPanel(null);
  };

  const unplug = () => {
    setNodesAndEdges(
      nodes,
      edges.filter((e: Edge) => !(e.target === nodeId && e.targetHandle === port.name)),
      true
    );
  };

  const set = (v: any) => updateNodeParams(nodeId, { [port.name]: v });

  // ----- Giá trị tệp -----
  const values: string[] = Array.isArray(value) ? value : value ? [value] : [];
  const Icon = kind ? KIND_ICON[kind] : Images;

  const addValue = (v: string) => {
    if (!v) return;
    if (multi) set([...values.filter((x) => x !== v), v]);
    else {
      set(v);
      setPanel(null);
    }
  };
  const removeValue = (v: string) => set(multi ? values.filter((x) => x !== v) : "");

  const togglePanel = async (p: Exclude<Panel, null>) => {
    const next = panel === p ? null : p;
    setPanel(next);
    if (next === "project" && kind && items === null) setItems(await fetchProjectLibrary(activeProjectId, kind));
  };

  const onFile = async (file: File) => {
    setErr(null);
    setBusy(true);
    try {
      const res = await uploadNodeFile(activeProjectId, file);
      addValue(res.uri);
      setItems(null);
    } catch (e: any) {
      setErr(e?.message || "Tải lên thất bại");
    } finally {
      setBusy(false);
    }
  };

  // ----- Nguồn: thuộc tính nhân vật -----
  const attrsOf = (c: any): CharAttr[] => {
    if (port.portType === "text") {
      const a: CharAttr[] = [
        { key: "name", label: "Tên", value: c.name },
        { key: "description", label: "Mô tả", value: c.description || "" },
        { key: "promptLock", label: "Prompt lock", value: c.promptLock || "" },
        { key: "voiceId", label: "Mã giọng", value: c.voiceId || "" },
        { key: "height", label: "Chiều cao", value: c.heightCm ? `${c.heightCm} cm` : "" },
      ];
      return a.filter((x) => x.value);
    }
    if (kind === "image") {
      const imgs: string[] = [c.primaryImage, ...(c.referenceImages || [])].filter(Boolean);
      return Array.from(new Set(imgs)).map((u, i) => ({
        key: `img${i}`,
        label: i === 0 ? "Ảnh chính" : `Ảnh tham chiếu ${i}`,
        value: u,
        image: true,
      }));
    }
    if (kind === "audio" && c.sampleAudioUrl) return [{ key: "sample", label: "Giọng mẫu", value: c.sampleAudioUrl }];
    return [];
  };
  const charList: any[] = characters || [];
  const hasCharSource = port.portType === "text" || kind === "image" || kind === "audio";
  const activeChar = charList.find((c) => c.id === charId) || charList[0];

  const pickAttr = (a: CharAttr) => {
    if (port.portType === "text") {
      set(a.value);
      setPanel(null);
    } else addValue(a.value);
  };

  // ----- Hiển thị -----
  const tabBtn = (id: Exclude<Panel, null>, label: string, IconC: any) => (
    <button
      key={id}
      type="button"
      onClick={() => togglePanel(id)}
      className={cn(
        "nodrag flex h-8 min-w-0 flex-1 items-center justify-center gap-1 rounded-md border text-xs text-foreground transition-colors hover:bg-accent",
        panel === id ? "border-foreground bg-accent" : "border-border bg-card"
      )}
    >
      <IconC className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{label}</span>
    </button>
  );

  const preview = (uri: string) => {
    const url = resolveNodeFileUrl(activeProjectId, uri);
    const name = uri.split("/").pop() || uri;
    return (
      <div key={uri} className="flex items-center gap-2 rounded-md border border-border bg-card p-1">
        {kind === "image" && url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={name} className="h-10 w-10 shrink-0 rounded object-cover object-top" />
        ) : (
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-muted text-muted-foreground">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <span className="min-w-0 flex-1 truncate text-[13px] text-foreground" title={name}>
          {name}
        </span>
        {kind === "audio" && url && <audio src={url} controls preload="none" className="nodrag h-6 w-24 shrink-0" />}
        <button
          type="button"
          onClick={() => removeValue(uri)}
          title="Bỏ"
          className="nodrag flex h-7 w-7 shrink-0 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  };

  // Đang nối dây
  if (incoming) {
    const srcNode = nodes.find((n: any) => n.id === incoming.source);
    return (
      <div className="flex items-center gap-2 rounded-md border border-dashed border-border bg-muted/30 px-2 py-1.5">
        <span className="min-w-0 flex-1 truncate text-[13px] text-foreground">
          {srcNode ? labelOf(srcNode) : incoming.source}
          <span className="text-muted-foreground"> · {incoming.sourceHandle}</span>
        </span>
        <button
          type="button"
          onClick={unplug}
          title="Gỡ dây nối"
          className="nodrag inline-flex h-7 shrink-0 items-center gap-1 rounded-md border border-border bg-card px-2 text-xs text-foreground transition-colors hover:bg-accent"
        >
          <Unlink className="h-3.5 w-3.5" />
          Gỡ dây
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {kind && (
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
      )}

      {port.portType === "text" && (
        <div className="relative">
          <textarea
            rows={2}
            value={typeof value === "string" ? value : ""}
            onChange={(e) => set(e.target.value)}
            placeholder={port.defaultValue ? String(port.defaultValue) : port.description || "Nhập nội dung…"}
            className="nodrag nowheel w-full resize-y rounded-md border border-border bg-card p-2 pr-7 text-xs leading-relaxed text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-brand"
          />
          {typeof value === "string" && value && (
            <button
              type="button"
              onClick={() => set("")}
              title="Xoá nội dung"
              className="nodrag absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      )}
      {kind && values.map(preview)}

      {(port.portType === "text" || multi || values.length === 0 || !kind) && (
        <div className="flex items-center gap-1.5">
          {tabBtn("node", "Node", Layers)}
          {kind && (
            <button
              type="button"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
              className="nodrag flex h-8 min-w-0 flex-1 items-center justify-center gap-1 rounded-md border border-border bg-card text-xs text-foreground transition-colors hover:bg-accent disabled:opacity-60"
            >
              <Upload className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{busy ? "Đang tải…" : "Tải lên"}</span>
            </button>
          )}
          {kind && tabBtn("project", "Dự án", FolderOpen)}
          {hasCharSource && tabBtn("character", "Nhân vật", Users)}
        </div>
      )}

      {/* Nguồn: output của node khác */}
      <Reveal show={panel === "node"}>
        <div className="space-y-1 rounded-md border border-border bg-muted/20 p-1.5">
          {candidates.length === 0 ? (
            <p className="p-2 text-center text-[13px] text-muted-foreground">Không có node nào có đầu ra phù hợp.</p>
          ) : (
            candidates.map((c) => (
              <button
                key={`${c.nodeId}:${c.port}`}
                type="button"
                onClick={() => connectTo(c)}
                className="nodrag flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-accent"
              >
                <span className="min-w-0 flex-1 truncate">{c.label}</span>
                <span className="shrink-0 font-mono text-[12px] text-muted-foreground">{c.port}</span>
              </button>
            ))
          )}
        </div>
      </Reveal>

      {/* Nguồn: tệp trong dự án */}
      <Reveal show={panel === "project"}>
        <div className="rounded-md border border-border bg-muted/20 p-1.5">
          {items === null ? (
            <p className="p-2 text-center text-[13px] text-muted-foreground">Đang tải…</p>
          ) : items.length === 0 ? (
            <p className="p-2 text-center text-[13px] text-muted-foreground">Dự án chưa có tệp loại này.</p>
          ) : (
            <div className="nowheel grid max-h-44 grid-cols-3 gap-1.5 overflow-y-auto">
              {items.map((it) => (
                <button
                  key={it.uri || it.url}
                  type="button"
                  onClick={() => addValue(it.uri || "")}
                  title={it.name}
                  className={cn(
                    "nodrag relative aspect-square overflow-hidden rounded border bg-card text-muted-foreground transition-colors hover:border-foreground",
                    values.includes(it.uri || "") ? "border-foreground" : "border-border"
                  )}
                >
                  {kind === "image" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={it.url} alt={it.name} loading="lazy" className="h-full w-full object-cover object-top" />
                  ) : (
                    <span className="flex h-full w-full flex-col items-center justify-center gap-1 p-1">
                      <Icon className="h-4 w-4" />
                      <span className="w-full truncate text-center text-[11px]">{it.name}</span>
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </Reveal>

      {/* Nguồn: thuộc tính nhân vật */}
      <Reveal show={panel === "character"}>
        <div className="space-y-1.5 rounded-md border border-border bg-muted/20 p-1.5">
          {charList.length === 0 ? (
            <p className="p-2 text-center text-[13px] text-muted-foreground">Dự án chưa có nhân vật.</p>
          ) : (
            <>
              <div className="flex flex-wrap gap-1">
                {charList.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setCharId(c.id)}
                    className={cn(
                      "nodrag rounded-full border px-2 py-0.5 text-xs transition-colors hover:bg-accent",
                      activeChar?.id === c.id ? "border-foreground bg-accent text-foreground" : "border-border bg-card text-muted-foreground"
                    )}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
              {activeChar && attrsOf(activeChar).length === 0 && (
                <p className="p-1 text-center text-[13px] text-muted-foreground">Nhân vật chưa có thuộc tính phù hợp.</p>
              )}
              {activeChar &&
                attrsOf(activeChar).map((a) => (
                  <button
                    key={a.key}
                    type="button"
                    onClick={() => pickAttr(a)}
                    className="nodrag flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-accent"
                  >
                    {a.image ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={resolveNodeFileUrl(activeProjectId, a.value)} alt="" className="h-8 w-8 shrink-0 rounded object-cover object-top" />
                    ) : null}
                    <span className="shrink-0 text-muted-foreground">{a.label}</span>
                    {!a.image && <span className="min-w-0 flex-1 truncate text-right">{a.value}</span>}
                  </button>
                ))}
            </>
          )}
        </div>
      </Reveal>

      {err && <p className="text-[13px] text-destructive">{err}</p>}
    </div>
  );
}
