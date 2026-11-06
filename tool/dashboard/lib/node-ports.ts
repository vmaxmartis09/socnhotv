import type { CapabilityDefinition, NodeDefinition, PortDefinition } from "@/lib/core-contracts";

/** Cổng ghi đè riêng của một node, lưu trong params._ports. */
export interface PortOverride {
  inputs?: PortDefinition[];
  outputs?: PortDefinition[];
}

export function getPortOverride(params?: Record<string, any>): PortOverride | null {
  const o = params?._ports;
  return o && typeof o === "object" ? (o as PortOverride) : null;
}

/** Chức năng có đang bật trong params không (params[name].enabled). */
export function isCapabilityEnabled(params: Record<string, any> | undefined, name: string): boolean {
  const own = params?.[name];
  return Boolean(own && typeof own === "object" && own.enabled);
}

export function enabledCapabilities(
  def: NodeDefinition | undefined,
  params?: Record<string, any>
): CapabilityDefinition[] {
  return (def?.capabilities || []).filter((c) => isCapabilityEnabled(params, c.name));
}

/**
 * Định nghĩa hiệu lực của một node (đồng bộ với NodeRegistry.effective_ports bên Core):
 * cổng gốc + cổng của các chức năng đang bật, rồi cổng ghi đè (params._ports) thắng; kèm tên riêng (nếu có).
 */
export function applyPortOverride(def: NodeDefinition, params?: Record<string, any>): NodeDefinition {
  const o = getPortOverride(params);
  const name = typeof params?._customName === "string" && params._customName ? params._customName : null;
  const caps = enabledCapabilities(def, params);
  if (!o && !name && caps.length === 0) return def;
  let inputs = def.inputPorts;
  let outputs = def.outputPorts;
  for (const c of caps) {
    const inNames = new Set(inputs.map((p) => p.name));
    const outNames = new Set(outputs.map((p) => p.name));
    inputs = [...inputs, ...(c.inputPorts || []).filter((p) => !inNames.has(p.name))];
    outputs = [...outputs, ...(c.outputPorts || []).filter((p) => !outNames.has(p.name))];
  }
  return {
    ...def,
    displayName: name || def.displayName,
    inputPorts: o?.inputs ?? inputs,
    outputPorts: o?.outputs ?? outputs,
  };
}

/**
 * Cổng ra chịu ảnh hưởng khi sửa params của node.
 * Chỉ khi MỌI khoá bị sửa là tham số của chức năng (params[<tên chức năng>]) mới thu hẹp được về cổng ra
 * của các chức năng đó; còn lại trả null = mọi cổng ra (như cũ).
 */
export function outputPortsAffectedByPatch(
  def: NodeDefinition | undefined,
  patch: Record<string, any>
): Set<string> | null {
  const caps = def?.capabilities || [];
  const keys = Object.keys(patch || {});
  if (!caps.length || !keys.length) return null;
  const ports = new Set<string>();
  for (const k of keys) {
    const cap = caps.find((c) => c.name === k);
    if (!cap) return null;
    for (const p of cap.outputPorts || []) ports.add(p.name);
  }
  return ports;
}
