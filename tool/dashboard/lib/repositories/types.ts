export interface Channel {
  id: string;
  name: string;
  platform: "youtube" | "tiktok" | "facebook" | "instagram" | "x";
  avatarUrl?: string;
  connected: boolean;
  defaultHashtags: string[];
  defaultPublishHours: string;
}

export interface CharacterMemory {
  personality: string;
  catchphrases: string[];
  habits: string[];
  pastEvents?: string[];
  pastEventsSummary: string[];
}

export interface CharacterImageAsset {
  id: string;
  url: string;
  angle: string;
  isPrimary: boolean;
  source: "upload" | "generated" | "master_dna";
  sourceType?: "upload" | "generated" | "master_dna";
  model?: string;
  prompt?: string;
  createdAt: string;
}

export type CharacterReferenceImage = CharacterImageAsset;

export interface CharacterClipAsset {
  id: string;
  url: string;
  thumbnailUrl?: string;
  episodeId: string;
  episodeTitle: string;
  sceneIndex?: number;
  sceneLabel: string;
  sceneTitle?: string;
  durationSec: number;
  model?: string;
  createdAt: string;
}

export type CharacterVideoClip = CharacterClipAsset;

export interface CharacterAppearance {
  episodeId: string;
  episodeTitle: string;
  scenes: string[];
}

export interface Character {
  id: string;
  projectId: string;
  name: string;
  role: "main" | "supporting";
  description?: string;
  heightCm: number;
  scaleRatio: number;
  voiceId: string;
  defaultTempo?: number;
  sampleAudioUrl?: string;
  voiceFiles?: { name: string; url: string; sizeKb: number }[];
  promptLock: string;
  primaryImage?: string;
  referenceImages: string[];
  referenceLibrary?: CharacterImageAsset[];
  generatedClips?: CharacterClipAsset[];
  appearances?: CharacterAppearance[];
  memory: CharacterMemory;
}

export interface Episode {
  id: string;
  projectId: string;
  episodeNumber: number;
  number?: number;
  title: string;
  durationSec?: number;
  scenesCount?: number;
  nodeCount: number;
  status: "ready" | "draft" | "published" | "rendering";
  updatedAt: string;
}

export interface ScheduledPost {
  id: string;
  projectId: string;
  episodeId: string;
  episodeTitle: string;
  title?: string;
  channelId: string;
  channelName: string;
  platform: "youtube" | "tiktok" | "facebook" | "instagram" | "x";
  scheduledAt: string;
  scheduledDate?: string;
  scheduledTime?: string;
  aspectRatio?: "9:16" | "16:9" | "1:1" | "4:5";
  status: "draft" | "pending_approval" | "approved" | "published";
  manualApprovalRequired: boolean;
  videoUri?: string;
}

export interface Scene {
  id: string;
  index: number;
  title: string;
  imagePrompt: string;
  videoPrompt: string;
  dialogueText: string;
  speakerId?: string;
  durationSec: number;
  transitionType?: string;
  generatedImageUrl?: string;
  generatedVideoUrl?: string;
  generatedAudioUrl?: string;
}

export interface Script {
  id: string;
  projectId: string;
  title: string;
  overview: string;
  scenes: Scene[];
}

export interface Job {
  id: string;
  projectId: string;
  nodeId?: string;
  type:
    | "image_gen"
    | "video_gen"
    | "voice_tts"
    | "script_analysis"
    | "render";
  model?: string;
  status: "pending" | "queued" | "running" | "completed" | "failed";
  progress: number;
  estimatedCostUsd: number;
  actualCostUsd: number;
  logs?: string[];
  outputUrl?: string;
  createdAt: string;
  completedAt?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  language: "vi" | "en";
  targetPlatforms: ("youtube" | "tiktok" | "instagram" | "facebook")[];
  defaultAspectRatio: "9:16" | "16:9" | "1:1" | "4:5";
  defaultCharacterId: string;
  defaultVoiceId: string;
  charactersCount: number;
  episodesCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface WorkspaceConfig {
  activeProjectId: string;
  theme: "light" | "dark" | "system";
  locale: "vi" | "en";
  maxConcurrentJobs: number;
  spendingLimitUsd: number;
  storageBackend: "local" | "supabase";
}

export interface IRepository {
  getWorkspaceConfig(): Promise<WorkspaceConfig>;
  saveWorkspaceConfig(config: Partial<WorkspaceConfig>): Promise<void>;

  listProjects(): Promise<Project[]>;
  getProject(id: string): Promise<Project | null>;
  saveProject(project: Project): Promise<void>;
  deleteProject(id: string): Promise<void>;

  listChannels(projectId?: string): Promise<Channel[]>;
  saveChannel(channel: Channel, projectId?: string): Promise<void>;

  listCharacters(projectId: string): Promise<Character[]>;
  saveCharacter(character: Character): Promise<void>;
  createCharacter(character: Character): Promise<void>;
  upsertCharacter(projectId: string, character: Character): Promise<Character>;
  deleteCharacter(projectId: string, id: string): Promise<void>;

  listScheduledPosts(projectId?: string): Promise<ScheduledPost[]>;
  saveScheduledPost(post: ScheduledPost, projectId?: string): Promise<void>;

  listJobs(projectId?: string): Promise<Job[]>;
  saveJob(job: Job): Promise<void>;
}
