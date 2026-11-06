export interface ShotItem {
  shotId: string;
  sceneNumber: number;
  sceneIndex: number;
  title: string;
  durationSec: number;
  startSec: number;
  endSec: number;
  dialogue: string;
  subtitle: string;
  speaker: string;
  speakerId: string;
  camera: string;
  priority: number;
  mediaSrc: string;
  enabled: boolean;
  isModified: boolean;
  action?: string;
  sfx?: string;
  bgm?: string;
}

export interface DecisionHistoryEntry {
  timestamp: string;
  action: string;
  shotId?: string;
  params?: Record<string, any>;
}

export interface EditDecisionsData {
  schemaVersion: number;
  episodeId: string;
  baseScriptSha256: string;
  createdAt: string;
  updatedAt: string;
  shotOrder: string[];
  shots: Record<string, Partial<ShotItem>>;
  history: DecisionHistoryEntry[];
}

export interface EditorEpisodeResponse {
  episodeId: string;
  title: string;
  aspect: string;
  baseDurationSec: number;
  effectiveDurationSec: number;
  hasDecisions: boolean;
  decisions: EditDecisionsData | null;
  shots: ShotItem[];
  outputVideoUrl: string | null;
  thumbUrl: string | null;
}

export interface RenderResult {
  status: "success" | "error";
  episodeId: string;
  outputVideo: string;
  videoUrl: string;
  thumbUrl?: string;
  renderedShotsCount: number;
  cachedShotsCount: number;
  totalShotsCount: number;
  elapsedSec: number;
  totalDurationSec: number;
  engine: string;
  message?: string;
}
