import type { NodeDefinition, PortDefinition } from "@/lib/core-contracts";

/** Cổng ghi đè riêng của một node, lưu trong params._ports. */
export interface PortOverride {
  inputs?: PortDefinition[];
  outputs?: PortDefinition[];
}

export function getPortOverride(params?: Record<string, any>): PortOverride | null {
  const o = params?._ports;
  return o && typeof o === "object" ? (o as PortOverride) : null;
}

/** Định nghĩa hiệu lực của một node: cổng ghi đè + tên riêng (nếu có). */
export function applyPortOverride(def: NodeDefinition, params?: Record<string, any>): NodeDefinition {
  const o = getPortOverride(params);
  const name = typeof params?._customName === "string" && params._customName ? params._customName : null;
  if (!o && !name) return def;
  return {
    ...def,
    displayName: name || def.displayName,
    inputPorts: o?.inputs ?? def.inputPorts,
    outputPorts: o?.outputs ?? def.outputPorts,
  };
}
