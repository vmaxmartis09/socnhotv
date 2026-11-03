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
  pastEventsSummary: string[];
}

export interface Character {
  id: string;
  projectId: string;
  name: string;
  role: "main" | "supporting";
  heightCm: number;
  scaleRatio: number;
  voiceId: string;
  promptLock: string;
  referenceImages: string[];
  memory: CharacterMemory;
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
  type: "image_gen" | "video_gen" | "voice_tts" | "script_analysis";
  model: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  estimatedCostUsd: number;
  actualCostUsd: number;
  logs: string[];
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

  listChannels(): Promise<Channel[]>;
  saveChannel(channel: Channel): Promise<void>;

  listCharacters(projectId: string): Promise<Character[]>;
  saveCharacter(character: Character): Promise<void>;

  listJobs(projectId?: string): Promise<Job[]>;
  saveJob(job: Job): Promise<void>;
}
