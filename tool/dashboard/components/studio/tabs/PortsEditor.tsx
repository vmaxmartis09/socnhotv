"use client";

import { useShallow } from "zustand/react/shallow";
import React, { useEffect, useMemo, useState } from "react";
import { useStudioStore, type StudioStore } from "@/store";
import type { NodeDefinition, PortDefinition, PortType } from "@/lib/core-contracts";
import { getPortOverride } from "@/lib/node-ports";
import { saveCustomNodeType } from "@/lib/core-api";
import { Plus, Trash2 } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const PORT_TYPES: PortType[] = [
  "text",
  "image",
  "image[]",
  "video",
  "audio",
  "script",
  "scenes",
  "character",
  "captions",
  "composition",
  "policy",
  "dialogue",
  "voice_clips",
];

const slug = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "");

type Side = "inputs" | "outputs";

interface RowProps {
  side: Side;
  p: PortDefinition;
  idx: number;
  mapOptions: string[];
  onChange: (side: Side, idx: number, patch: Partial<PortDefinition>) => void;
  onRemove: (side: Side, idx: number) => void;
}

function PortRow({ side, p, idx, mapOptions, onChange, onRemove }: RowProps) {
  const field = "h-8 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand";
  return (
    <div className="space-y-2 rounded-md border border-border p-2">
      <div className="flex items-center gap-1.5">
        <input
          value={p.name}
          onChange={(e) => onChange(side, idx, { name: e.target.value.trim() })}
          aria-label="Tên cổng"
          className={cn(field, "min-w-0 flex-1 font-mono")}
        />
        <select
          value={p.portType}
          onChange={(e) => onChange(side, idx, { portType: e.target.value as PortType })}
          aria-label="Kiểu dữ liệu"
          className={cn(field, "w-[96px] shrink-0 font-mono")}
        >
          {PORT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => onRemove(side, idx)}
          title="Xoá cổng"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-x-2 gap-y-1.5">
        <label className="block space-y-1">
          <span className="text-[13px] text-muted-foreground">Ánh xạ về</span>
          <select
            value={p.mapTo || ""}
            onChange={(e) => onChange(side, idx, { mapTo: e.target.value || undefined })}
            className={cn(field, "w-full truncate font-mono")}
          >
            <option value="">— không —</option>
            {mapOptions.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        {side === "inputs" && p.portType === "text" ? (
          <label className="block space-y-1">
            <span className="text-[13px] text-muted-foreground">Giá trị mặc định</span>
            <input
              value={typeof p.defaultValue === "string" ? p.defaultValue : ""}
              onChange={(e) => onChange(side, idx, { defaultValue: e.target.value || undefined })}
              placeholder="(trống)"
              className={cn(field, "w-full")}
            />
          </label>
        ) : (
          <span />
        )}
        {side === "inputs" && (
          <label className="col-span-2 flex items-center gap-1.5 text-[13px] text-muted-foreground">
            <input
              type="checkbox"
              checked={p.required !== false}
              onChange={(e) => onChange(side, idx, { required: e.target.checked })}
            />
            Bắt buộc có dữ liệu
          </label>
        )}
      </div>
    </div>
  );
}

/** Tuỳ biến cổng vào / ra của một node: lưu riêng cho node, hoặc tách thành loại node mới. */
export function PortsEditor({
  nodeId,
  baseDef,
  params,
}: {
  nodeId: string;
  baseDef: NodeDefinition;
  params: Record<string, any>;
}) {
  const { nodes, edges, setNodesAndEdges, activeProjectId, refreshCustomNodeTypes } = useStudioStore(
    useShallow((s: StudioStore) => ({
      nodes: s.nodes,
      edges: s.edges,
      setNodesAndEdges: s.setNodesAndEdges,
      activeProjectId: s.activeProjectId,
      refreshCustomNodeTypes: s.refreshCustomNodeTypes,
    }))
  ) as any;
  const override = getPortOverride(params);
  const current = useMemo(
    () => ({
      inputs: (override?.inputs ?? baseDef.inputPorts) as PortDefinition[],
      outputs: (override?.outputs ?? baseDef.outputPorts) as PortDefinition[],
    }),
    [override, baseDef]
  );

  const [inputs, setInputs] = useState<PortDefinition[]>(current.inputs);
  const [outputs, setOutputs] = useState<PortDefinition[]>(current.outputs);
  const [title, setTitle] = useState<string>(params._customName || "");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [saveAs, setSaveAs] = useState(false);
  const [newName, setNewName] = useState("");
  const [scope, setScope] = useState<"project" | "shared">("project");
  const [busy, setBusy] = useState(false);

  // Đồng bộ lại khi đổi node hoặc cổng đã lưu thay đổi
  useEffect(() => {
    setInputs(current.inputs);
    setOutputs(current.outputs);
    setTitle(params._customName || "");
    setError(null);
    setSaveAs(false);
  }, [nodeId, current, params._customName]);

  const dirty =
    JSON.stringify(inputs) !== JSON.stringify(current.inputs) ||
    JSON.stringify(outputs) !== JSON.stringify(current.outputs) ||
    title !== (params._customName || "");

  const update = (side: Side, idx: number, patch: Partial<PortDefinition>) => {
    const setter = side === "inputs" ? setInputs : setOutputs;
    setter((list) => list.map((p, i) => (i === idx ? { ...p, ...patch } : p)));
    setInfo(null);
  };
  const remove = (side: Side, idx: number) => {
    const setter = side === "inputs" ? setInputs : setOutputs;
    setter((list) => list.filter((_, i) => i !== idx));
    setInfo(null);
  };
  const add = (side: Side) => {
    const prefix = side === "inputs" ? "in" : "out";
    const setter = side === "inputs" ? setInputs : setOutputs;
    setter((list) => {
      let n = list.length + 1;
      while (list.some((p) => p.name === `${prefix}_${n}`)) n++;
      return [...list, { name: `${prefix}_${n}`, portType: "text" as PortType, required: false }];
    });
    setInfo(null);
  };

  const validate = (): string | null => {
    for (const [label, list] of [["vào", inputs], ["ra", outputs]] as const) {
      const names = new Set<string>();
      for (const p of list) {
        if (!p.name || slug(p.name) !== p.name) return `Tên cổng ${label} chỉ gồm a-z, 0-9, _ (đang là "${p.name}").`;
        if (names.has(p.name)) return `Trùng tên cổng ${label}: "${p.name}".`;
        names.add(p.name);
      }
    }
    return null;
  };

  const applyToNode = () => {
    const err = validate();
    if (err) return setError(err);
    setError(null);
    const inNames = new Set(inputs.map((p) => p.name));
    const outNames = new Set(outputs.map((p) => p.name));
    // Gỡ dây nối vào các cổng đã bị xoá / đổi tên
    const nextEdges = edges.filter(
      (e: any) =>
        !(e.target === nodeId && !inNames.has(e.targetHandle)) &&
        !(e.source === nodeId && !outNames.has(e.sourceHandle))
    );
    const removed = edges.length - nextEdges.length;
    const nextNodes = nodes.map((n: any) =>
      n.id === nodeId
        ? {
            ...n,
            data: {
              ...n.data,
              params: { ...n.data.params, _ports: { inputs, outputs }, _customName: title.trim() || undefined },
            },
          }
        : n
    );
    setNodesAndEdges(nextNodes, nextEdges, true);
    setInfo(removed > 0 ? `Đã lưu cho node này (gỡ ${removed} dây nối vào cổng đã xoá).` : "Đã lưu cho node này.");
  };

  const reset = () => {
    const nextEdges = edges.filter(
      (e: any) =>
        !(e.target === nodeId && !baseDef.inputPorts.some((p) => p.name === e.targetHandle)) &&
        !(e.source === nodeId && !baseDef.outputPorts.some((p) => p.name === e.sourceHandle))
    );
    const nextNodes = nodes.map((n: any) => {
      if (n.id !== nodeId) return n;
      const { _ports, _customName, ...rest } = n.data.params || {};
      return { ...n, data: { ...n.data, params: rest } };
    });
    setNodesAndEdges(nextNodes, nextEdges, true);
    setInfo("Đã khôi phục cổng mặc định.");
  };

  const saveAsNewType = async () => {
    const err = validate();
    if (err) return setError(err);
    const name = newName.trim();
    if (!name) return setError("Nhập tên cho loại node mới.");
    setError(null);
    setBusy(true);
    try {
      const keep = Object.fromEntries(Object.entries(params).filter(([k]) => !k.startsWith("_")));
      const def: NodeDefinition = {
        typeName: `custom:${slug(name) || "node"}`,
        displayName: name,
        category: baseDef.category,
        description: baseDef.description,
        inputPorts: inputs,
        outputPorts: outputs,
        defaultParams: { ...baseDef.defaultParams, ...keep },
        mockable: baseDef.mockable,
        baseType: baseDef.typeName,
      };
      await saveCustomNodeType(def, scope, activeProjectId);
      await refreshCustomNodeTypes(activeProjectId);
      setInfo(`Đã lưu loại node "${name}" (${scope === "shared" ? "dùng chung" : "theo dự án"}). Tìm trong menu thêm node.`);
      setSaveAs(false);
      setNewName("");
    } catch (e: any) {
      setError(e?.message || "Lưu thất bại");
    } finally {
      setBusy(false);
    }
  };

  const inMapOptions = [...baseDef.inputPorts.map((p) => p.name), ...Object.keys(baseDef.defaultParams || {})];
  const outMapOptions = baseDef.outputPorts.map((p) => p.name);

  const renderBlock = (side: Side, label: string) => {
    const list = side === "inputs" ? inputs : outputs;
    return (
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">{label}</span>
          <button
            type="button"
            onClick={() => add(side)}
            className="inline-flex items-center gap-1 rounded border border-border bg-card px-1.5 py-0.5 text-xs text-foreground hover:bg-accent"
          >
            <Plus className="h-3 w-3" /> Thêm
          </button>
        </div>
        {list.length === 0 && <p className="text-[13px] text-muted-foreground">Chưa có cổng.</p>}
        {list.map((p, i) => (
          <PortRow
            key={`${side}:${i}`}
            side={side}
            p={p}
            idx={i}
            mapOptions={side === "inputs" ? inMapOptions : outMapOptions}
            onChange={update}
            onRemove={remove}
          />
        ))}
      </div>
    );
  };

  return (
    <section className="space-y-3 border-b border-border pb-3.5">
      <h4 className="font-semibold text-foreground">Cổng vào / ra</h4>
      <p className="text-[13px] leading-relaxed text-muted-foreground">
        Cổng thêm cần <b>ánh xạ</b> về cổng/tham số của node gốc ({baseDef.typeName}) mới có tác dụng khi chạy.
      </p>
      <label className="block space-y-1">
        <span className="text-muted-foreground">Tên hiển thị của node này</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={baseDef.displayName}
          className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs focus:outline-none focus:ring-1 focus:ring-brand"
        />
      </label>
      {renderBlock("inputs", "Đầu vào")}
      {renderBlock("outputs", "Đầu ra")}

      {error && <p className="rounded bg-destructive/10 p-1.5 text-[13px] text-destructive">{error}</p>}
      {info && <p className="rounded bg-muted p-1.5 text-[13px] text-foreground">{info}</p>}

      <div className="flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          disabled={!dirty}
          onClick={applyToNode}
          className={cn(
            "h-8 rounded-md px-3 text-xs font-medium",
            dirty ? "bg-foreground text-background hover:opacity-90" : "bg-muted text-muted-foreground"
          )}
        >
          Lưu cho node này
        </button>
        <button
          type="button"
          onClick={() => setSaveAs((v) => !v)}
          className="h-8 rounded-md border border-border px-3 text-xs text-foreground hover:bg-accent"
        >
          Lưu thành loại node mới…
        </button>
        {(override || params._customName) && (
          <button type="button" onClick={reset} className="h-8 rounded-md px-2 text-xs text-muted-foreground hover:text-foreground">
            Khôi phục mặc định
          </button>
        )}
      </div>

      {saveAs && (
        <div className="space-y-2 rounded-md border border-border bg-muted/30 p-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Tên loại node mới"
            className="h-8 w-full rounded-md border border-border bg-card px-2 text-xs focus:outline-none focus:ring-1 focus:ring-brand"
          />
          <div className="flex items-center gap-3 text-[13px] text-foreground">
            <label className="flex items-center gap-1">
              <input type="radio" checked={scope === "project"} onChange={() => setScope("project")} /> Dự án này
            </label>
            <label className="flex items-center gap-1">
              <input type="radio" checked={scope === "shared"} onChange={() => setScope("shared")} /> Dùng chung
            </label>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={saveAsNewType}
            className="h-8 rounded-md bg-foreground px-3 text-xs font-medium text-background hover:opacity-90 disabled:opacity-50"
          >
            {busy ? "Đang lưu…" : "Lưu loại node"}
          </button>
        </div>
      )}
    </section>
  );
}
