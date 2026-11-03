import { openDB, type IDBPDatabase } from "idb";
import type {
  IRepository,
  Project,
  Channel,
  Character,
  Job,
  WorkspaceConfig,
} from "./types";

const DB_NAME = "ai_video_studio_local_v1";
const DB_VERSION = 1;

// Default initial project based on SocNhoTV data
const INITIAL_PROJECTS: Project[] = [
  {
    id: "soc-nho-tv",
    name: "Sóc Nhỏ TV",
    description: "Kênh hoạt hình 3D giáo dục kỹ năng và khám phá cho trẻ em",
    language: "vi",
    targetPlatforms: ["youtube", "tiktok"],
    defaultAspectRatio: "9:16",
    defaultCharacterId: "soc_nho",
    defaultVoiceId: "soc-nho",
    charactersCount: 2,
    episodesCount: 1,
    createdAt: "2026-11-03T00:00:00.000Z",
    updatedAt: "2026-11-03T00:00:00.000Z",
  },
];

const INITIAL_CHARACTERS: Character[] = [
  {
    id: "soc_nho",
    projectId: "soc-nho-tv",
    name: "Sóc Nhỏ (Bi)",
    role: "main",
    heightCm: 100,
    scaleRatio: 1.0,
    voiceId: "soc-nho",
    promptLock:
      "A cute 3D Pixar-style baby squirrel named Bi, fluffy tail, cheerful expression, 100cm height lock.",
    referenceImages: [
      "/demo/characters/soc_nho_01.png",
      "/demo/characters/soc_nho_02.png",
    ],
    memory: {
      personality: "Tò mò, vui vẻ, thích học hỏi, hay quên đánh răng",
      catchphrases: ["Chào các bạn, mình là Bi nè!", "Oa, tuyệt vời quá!"],
      habits: ["Thích ăn hạt dẻ và kẹo ngọt", "Luôn vẫy đuôi khi hào hứng"],
      pastEventsSummary: ["Tập 1: Đi khám răng và học cách đánh răng đúng cách"],
    },
  },
  {
    id: "koala",
    projectId: "soc-nho-tv",
    name: "Bạn Koala",
    role: "supporting",
    heightCm: 150,
    scaleRatio: 1.5,
    voiceId: "voice-koala",
    promptLock:
      "A friendly 3D Pixar-style Koala bear friend, gentle, calm posture, 150cm height lock.",
    referenceImages: [],
    memory: {
      personality: "Hiền lành, điềm đạm, thường khuyên nhủ Bi",
      catchphrases: ["Cẩn thận nhé Bi ơi!", "Phải nhớ lời bác sĩ dặn nhé."],
      habits: ["Đi lại từ tốn, thích ăn lá bạch đàn"],
      pastEventsSummary: ["Đã đồng hành cùng Bi đến phòng khám răng"],
    },
  },
];

const INITIAL_CHANNELS: Channel[] = [
  {
    id: "chan_yt_1",
    name: "Sóc Nhỏ TV Official",
    platform: "youtube",
    connected: true,
    defaultHashtags: ["#SocNhoTV", "#HoatHinh3D", "#ThieuNhi"],
    defaultPublishHours: "19:00",
  },
  {
    id: "chan_tt_1",
    name: "@socnhotv.official",
    platform: "tiktok",
    connected: true,
    defaultHashtags: ["#socnhotv", "#cartoon3d", "#learnontiktok"],
    defaultPublishHours: "20:00",
  },
];

const INITIAL_WORKSPACE: WorkspaceConfig = {
  activeProjectId: "soc-nho-tv",
  theme: "system",
  locale: "vi",
  maxConcurrentJobs: 3,
  spendingLimitUsd: 15.0,
  storageBackend: "local",
};

export class LocalRepository implements IRepository {
  private memoryProjects: Map<string, Project> = new Map(
    INITIAL_PROJECTS.map((p) => [p.id, p])
  );
  private memoryCharacters: Map<string, Character> = new Map(
    INITIAL_CHARACTERS.map((c) => [c.id, c])
  );
  private memoryChannels: Map<string, Channel> = new Map(
    INITIAL_CHANNELS.map((ch) => [ch.id, ch])
  );
  private memoryJobs: Map<string, Job> = new Map();
  private memoryConfig: WorkspaceConfig = { ...INITIAL_WORKSPACE };

  private isBrowser(): boolean {
    return typeof window !== "undefined" && "indexedDB" in window;
  }

  private async getDB(): Promise<IDBPDatabase | null> {
    if (!this.isBrowser()) return null;

    return openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains("projects")) {
          const store = db.createObjectStore("projects", { keyPath: "id" });
          INITIAL_PROJECTS.forEach((p) => store.add(p));
        }
        if (!db.objectStoreNames.contains("characters")) {
          const store = db.createObjectStore("characters", { keyPath: "id" });
          INITIAL_CHARACTERS.forEach((c) => store.add(c));
        }
        if (!db.objectStoreNames.contains("channels")) {
          const store = db.createObjectStore("channels", { keyPath: "id" });
          INITIAL_CHANNELS.forEach((ch) => store.add(ch));
        }
        if (!db.objectStoreNames.contains("jobs")) {
          db.createObjectStore("jobs", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("config")) {
          const store = db.createObjectStore("config", { keyPath: "id" });
          store.add({ id: "current", ...INITIAL_WORKSPACE });
        }
      },
    });
  }

  async getWorkspaceConfig(): Promise<WorkspaceConfig> {
    const db = await this.getDB();
    if (!db) return this.memoryConfig;
    const config = await db.get("config", "current");
    return config || this.memoryConfig;
  }

  async saveWorkspaceConfig(config: Partial<WorkspaceConfig>): Promise<void> {
    this.memoryConfig = { ...this.memoryConfig, ...config };
    const db = await this.getDB();
    if (db) {
      await db.put("config", { id: "current", ...this.memoryConfig });
    }
  }

  async listProjects(): Promise<Project[]> {
    const db = await this.getDB();
    if (!db) return Array.from(this.memoryProjects.values());
    const items = await db.getAll("projects");
    return items.length > 0 ? items : Array.from(this.memoryProjects.values());
  }

  async getProject(id: string): Promise<Project | null> {
    const db = await this.getDB();
    if (!db) return this.memoryProjects.get(id) || null;
    const item = await db.get("projects", id);
    return item || this.memoryProjects.get(id) || null;
  }

  async saveProject(project: Project): Promise<void> {
    this.memoryProjects.set(project.id, project);
    const db = await this.getDB();
    if (db) {
      await db.put("projects", project);
    }
  }

  async deleteProject(id: string): Promise<void> {
    this.memoryProjects.delete(id);
    const db = await this.getDB();
    if (db) {
      await db.delete("projects", id);
    }
  }

  async listChannels(): Promise<Channel[]> {
    const db = await this.getDB();
    if (!db) return Array.from(this.memoryChannels.values());
    const items = await db.getAll("channels");
    return items.length > 0 ? items : Array.from(this.memoryChannels.values());
  }

  async saveChannel(channel: Channel): Promise<void> {
    this.memoryChannels.set(channel.id, channel);
    const db = await this.getDB();
    if (db) {
      await db.put("channels", channel);
    }
  }

  async listCharacters(projectId: string): Promise<Character[]> {
    const db = await this.getDB();
    const all = db
      ? await db.getAll("characters")
      : Array.from(this.memoryCharacters.values());
    return all.filter((c) => c.projectId === projectId);
  }

  async saveCharacter(character: Character): Promise<void> {
    this.memoryCharacters.set(character.id, character);
    const db = await this.getDB();
    if (db) {
      await db.put("characters", character);
    }
  }

  async listJobs(projectId?: string): Promise<Job[]> {
    const db = await this.getDB();
    const all = db
      ? await db.getAll("jobs")
      : Array.from(this.memoryJobs.values());
    if (!projectId) return all;
    return all.filter((j) => j.projectId === projectId);
  }

  async saveJob(job: Job): Promise<void> {
    this.memoryJobs.set(job.id, job);
    const db = await this.getDB();
    if (db) {
      await db.put("jobs", job);
    }
  }
}
