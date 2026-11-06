/**
 * Tệp này được sinh tự động từ socnhotv.core.contracts.types.
 * TUYỆT ĐỐI KHÔNG SỬA TAY ĐỂ TRÁNH LỆCH KIỂU GIỮA PYTHON CORE VÀ NEXT.JS UI.
 */

export type PortType =
  | "text"
  | "image"
  | "image[]"
  | "video"
  | "audio"
  | "script"
  | "scenes"
  | "character"
  | "captions"
  | "composition"
  | "policy"
  /** Lời thoại có người nói: [{id, speaker, characterId, text, shotId, sceneIndex, startSec, endSec, delivery}] */
  | "dialogue"
  /** Câu thoại đã đọc (từng clip) từ chức năng Nói của nhân vật → cổng voice_clips của bộ dựng */
  | "voice_clips";

export type ArtifactKind =
  | "image"
  | "video"
  | "audio"
  | "text"
  | "captions"
  | "composition";

export type NodeState =
  | "idle"
  | "ready"
  | "queued"
  | "running"
  | "succeeded"
  | "completed"
  | "failed"
  | "skipped"
  | "cancelled"
  | "cached"
  | "stale";

export type NodeStatus = NodeState;

export type SSEEventType =
  | "run_started"
  | "node_state"
  | "node_progress"
  | "node_log"
  | "cost_update"
  | "run_completed"
  | "run_failed";

export type RunMode =
  | "all"
  | "force_all"
  | "single"
  | "single_node"
  | "downstream";

export interface ArtifactMeta {
  width?: number;
  height?: number;
  duration?: number;
  fps?: number;
  aspect?: string;
}

export interface ArtifactProvenance {
  nodeId: string;
  runId?: string;
  provider: string;
  model: string;
  params?: Record<string, any>;
  inputHashes?: string[];
  costUsd: number;
  createdAt: string;
}

export interface Artifact {
  id: string;
  kind: ArtifactKind;
  uri: string;
  mime: string;
  size: number;
  hash: string;
  meta: ArtifactMeta;
  provenance: ArtifactProvenance;
}

export interface Generation {
  id: string;
  nodeId: string;
  params: Record<string, any>;
  artifactId: string;
  costUsd: number;
  createdAt: string;
  isPinned: boolean;
}

export interface PortDefinition {
  name: string;
  portType: PortType;
  description?: string;
  required?: boolean;
  /** Cổng tuỳ biến: ánh xạ về cổng/tham số của node gốc */
  mapTo?: string;
  /** Giá trị mặc định khi không nối dây và chưa nhập */
  defaultValue?: any;
}

export interface NodeDefinition {
  typeName: string;
  displayName: string;
  category: string;
  description: string;
  inputPorts: PortDefinition[];
  outputPorts: PortDefinition[];
  defaultParams: Record<string, any>;
  mockable: boolean;
  /** Loại node tuỳ biến: biến thể của node gốc (dùng chung bộ chạy) */
  baseType?: string;
  scope?: "project" | "shared";
  /** Chức năng bật/tắt được trong node (vd. Nhân vật: Nói, Ảnh theo cảnh). Bật bằng params[name].enabled */
  capabilities?: CapabilityDefinition[];
}

export interface CapabilityDefinition {
  name: string;
  displayName: string;
  description?: string;
  inputPorts: PortDefinition[];
  outputPorts: PortDefinition[];
  defaultParams: Record<string, any>;
  /** false = đã khai báo nhưng bộ chạy chưa có, không cho bật */
  available?: boolean;
}

export interface NodePortInputRef {
  nodeId: string;
  outputPort: string;
}

export interface NodeInstance {
  id: string;
  type: string;
  params: Record<string, any>;
  inputs?: Record<string, NodePortInputRef | any>;
  position: { x: number; y: number };
  ui?: Record<string, any>;
  state?: NodeState;
  status?: NodeState;
  isStale: boolean;
  pinnedGenerationId?: string | null;
  generations?: Generation[];
}

export interface Edge {
  id: string;
  sourceNodeId: string;
  sourcePort: string;
  targetNodeId: string;
  targetPort: string;
}

export interface Graph {
  id: string;
  projectId: string;
  name?: string;
  nodes: NodeInstance[];
  edges: Edge[];
  updatedAt?: string;
}

export interface SSEEvent {
  eventType: SSEEventType;
  runId: string;
  nodeId?: string;
  state?: NodeState;
  progress?: number;
  message?: string;
  costUsd?: number;
  timestamp: string;
}

export interface RunPolicy {
  image: "mock" | "real";
  video: "off" | "mock" | "real";
  text: "mock" | "real";
  voice: "local" | "mock";
}

export type RunPresetMode = "quick" | "animatic" | "full" | "custom";

export const RUN_PRESETS: Record<Exclude<RunPresetMode, "custom">, RunPolicy> = {
  quick: { image: "mock", video: "mock", text: "mock", voice: "mock" },
  animatic: { image: "real", video: "off", text: "mock", voice: "local" },
  full: { image: "real", video: "real", text: "real", voice: "local" },
};

export function getRunPresetMode(policy: RunPolicy): RunPresetMode {
  if (
    policy.image === "mock" &&
    policy.video === "mock" &&
    policy.text === "mock" &&
    policy.voice === "mock"
  ) {
    return "quick";
  }
  if (
    policy.image === "real" &&
    policy.video === "off" &&
    policy.text === "mock" &&
    policy.voice === "local"
  ) {
    return "animatic";
  }
  if (
    policy.image === "real" &&
    policy.video === "real" &&
    policy.text === "real" &&
    policy.voice === "local"
  ) {
    return "full";
  }
  return "custom";
}

export interface GraphRunRequest {
  projectId: string;
  graphId?: string;
  mode?: RunMode;
  targetNodeId?: string;
  spendingLimitUsd?: number;
  mockMode?: boolean;
  runPolicy?: RunPolicy;
  confirmPaidRun?: boolean;
  maxRetries?: number;
  concurrencyLimit?: number;
}

export interface GraphValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  topologicalOrder: string[];
}

export interface GraphRunSummary {
  runId: string;
  projectId: string;
  totalNodes: number;
  executedNodes: string[];
  skippedNodes: string[];
  failedNodes: string[];
  totalCostUsd: number;
  isSuccess: boolean;
  errors: Record<string, string>;
  /** Node con bị đánh dấu lỗi thời sau lượt chạy (chỉ con nối vào cổng ra có dữ liệu đổi) */
  staleNodes?: string[];
}
