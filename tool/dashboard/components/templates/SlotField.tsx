"use client";

import React from "react";
import type { Slot } from "@/lib/api/video";

export interface SlotFieldProps {
  slot: Slot;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  projectId?: string;
}

export function SlotField({ slot, value, onChange, error, projectId }: SlotFieldProps) {
  const currentVal = value ?? slot.default ?? "";

  // 1. Text field
  if (slot.type === "text") {
    const strVal = String(currentVal);
    const charCount = strVal.length;
    const isLong = (slot.max_chars || 0) > 80;

    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-foreground">
            {slot.label || slot.key}
            {slot.required && <span className="ml-1 text-semantic-danger">*</span>}
          </label>
          {slot.max_chars && (
            <span
              className={`text-[11px] ${
                charCount > slot.max_chars ? "font-bold text-semantic-danger" : "text-muted-foreground"
              }`}
            >
              {charCount}/{slot.max_chars}
            </span>
          )}
        </div>

        {isLong ? (
          <textarea
            value={strVal}
            rows={3}
            onChange={(e) => onChange(e.target.value)}
            placeholder={slot.description || `Nhập ${slot.label || slot.key}...`}
            className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-primary"
          />
        ) : (
          <input
            type="text"
            value={strVal}
            onChange={(e) => onChange(e.target.value)}
            placeholder={slot.description || `Nhập ${slot.label || slot.key}...`}
            className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
          />
        )}

        {error && <p className="text-xs text-semantic-danger">{error}</p>}
      </div>
    );
  }

  // 2. Product field
  if (slot.type === "product") {
    const productObj = typeof currentVal === "object" && currentVal !== null ? currentVal : {};
    return (
      <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5">
        <label className="text-xs font-semibold text-foreground">
          🛍️ {slot.label || slot.key}
          {slot.required && <span className="ml-1 text-semantic-danger">*</span>}
        </label>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <input
            type="text"
            placeholder="Tên sản phẩm..."
            value={productObj.title || productObj.name || ""}
            onChange={(e) => onChange({ ...productObj, title: e.target.value })}
            className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
          />
          <input
            type="text"
            placeholder="Giá sản phẩm (vd: 149.000đ)..."
            value={productObj.price || ""}
            onChange={(e) => onChange({ ...productObj, price: e.target.value })}
            className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
          />
        </div>
        {error && <p className="text-xs text-semantic-danger">{error}</p>}
      </div>
    );
  }

  // 3. Media list (media[])
  if (slot.type === "media[]" || slot.type === "list") {
    const listVal: string[] = Array.isArray(currentVal) ? currentVal : [];
    return (
      <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-foreground">
            🎞️ {slot.label || slot.key}
            {slot.required && <span className="ml-1 text-semantic-danger">*</span>}
          </label>
          <span className="text-[11px] text-muted-foreground">
            {listVal.length} mục {slot.max ? `(tối đa ${slot.max})` : ""}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          {listVal.map((item, idx) => (
            <div key={`${slot.key}-${idx}`} className="flex items-center gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => {
                  const updated = [...listVal];
                  updated[idx] = e.target.value;
                  onChange(updated);
                }}
                className="flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground outline-none focus:border-primary"
              />
              <button
                type="button"
                onClick={() => onChange(listVal.filter((_, i) => i !== idx))}
                className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-semantic-danger"
              >
                ✕
              </button>
            </div>
          ))}

          <button
            type="button"
            onClick={() => onChange([...listVal, ""])}
            className="flex items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-2 text-xs text-muted-foreground hover:border-primary hover:text-primary transition-colors"
          >
            + Thêm đường dẫn media
          </button>
        </div>
        {error && <p className="text-xs text-semantic-danger">{error}</p>}
      </div>
    );
  }

  // Fallback generic input
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-foreground">
        {slot.label || slot.key}
        {slot.required && <span className="ml-1 text-semantic-danger">*</span>}
      </label>
      <input
        type="text"
        value={String(currentVal)}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
      />
      {error && <p className="text-xs text-semantic-danger">{error}</p>}
    </div>
  );
}
