import { openDB, type IDBPDatabase } from "idb";
import type {
  IRepository,
  Project,
  Channel,
  Character,
  ScheduledPost,
  Job,
  WorkspaceConfig,
} from "./types";

const DB_NAME = "ai_video_studio_local_v2";
const DB_VERSION = 1;

const INITIAL_PROJECTS: Project[] = [
  {
    id: "soc-nho-tv",
    name: "Sóc Nhỏ TV",
    description:
      "Kênh hoạt hình 3D giáo dục kỹ năng và khám phá thế giới cho trẻ em",
    language: "vi",
    targetPlatforms: ["youtube", "tiktok"],
    defaultAspectRatio: "9:16",
    defaultCharacterId: "soc_nho",
    defaultVoiceId: "soc-nho",
    charactersCount: 2,
    episodesCount: 3,
    createdAt: "2026-11-01T17:29:00.000Z",
    updatedAt: "2026-11-03T15:28:00.000Z",
  },
];

const INITIAL_CHARACTERS: Character[] = [
  {
    id: "soc_nho",
    projectId: "soc-nho-tv",
    name: "Sóc Nhỏ (Bi)",
    role: "main",
    description:
      "Thon gọn, nhanh nhẹn, khỏe khoắn như trẻ 3-4 tuổi hay chạy nhảy (KHÔNG béo, KHÔNG phình). Áo phông vàng cổ tròn, quần short đen, giày thể thao tối màu.",
    heightCm: 100,
    scaleRatio: 1.0,
    voiceId: "soc-nho",
    defaultTempo: 1.1,
    sampleAudioUrl: "/demo/audio/soc-nho_sample.mp3",
    promptLock:
      "Bé sóc nam, 3-4 tuổi, cao ~100cm nặng ~15kg, thân hình THON GỌN, ốm khỏe, nhanh nhẹn như trẻ hay chạy nhảy, KHÔNG béo, bụng phẳng, thân nhỏ gọn, tay chân ngắn thon, đầu to vừa phải khoảng 1/4 thân, lông nâu đỏ cam, mắt đen tròn to, má hồng nhẹ, hai răng cửa, đuôi xù lớn, áo phông vàng vừa người, quần short đen, giày thể thao tối màu, 3D Pixar, ánh sáng studio mềm, nền trơn sáng",
    referenceImages: [
      "/demo/characters/soc_nho_01.png",
      "/demo/characters/soc_nho_02.png",
      "/demo/characters/soc_nho_03.png",
      "/demo/characters/soc_nho_04.png",
      "/demo/characters/soc_nho_05.png",
      "/demo/characters/soc_nho_06.png",
    ],
    referenceLibrary: [
      {
        id: "ref_soc_nho_01",
        url: "/demo/characters/soc_nho_01.png",
        angle: "Chính diện vẫy tay (Master DNA)",
        isPrimary: true,
        source: "master_dna",
        sourceType: "master_dna",
        model: "gemini-2.5-flash-image",
        prompt: "assets/soc_nho/soc_nho_01.png — Khóa chiều cao 100 cm",
        createdAt: "2026-11-01T17:30:00.000Z",
      },
      {
        id: "ref_soc_nho_02",
        url: "/demo/characters/soc_nho_02.png",
        angle: "Góc nghiêng 3/4 trái",
        isPrimary: false,
        source: "master_dna",
        sourceType: "master_dna",
        model: "gemini-2.5-flash-image",
        prompt: "assets/soc_nho/soc_nho_02.png — Khóa chiều cao 100 cm",
        createdAt: "2026-11-01T17:30:30.000Z",
      },
      {
        id: "ref_soc_nho_03",
        url: "/demo/characters/soc_nho_03.png",
        angle: "Góc nghiêng 3/4 phải",
        isPrimary: false,
        source: "master_dna",
        sourceType: "master_dna",
        model: "gemini-2.5-flash-image",
        prompt: "assets/soc_nho/soc_nho_03.png — Khóa chiều cao 100 cm",
        createdAt: "2026-11-01T17:31:00.000Z",
      },
      {
        id: "ref_soc_nho_04",
        url: "/demo/characters/soc_nho_04.png",
        angle: "Nhìn từ sau (đuôi xù cong)",
        isPrimary: false,
        source: "master_dna",
        sourceType: "master_dna",
        model: "gemini-2.5-flash-image",
        prompt: "assets/soc_nho/soc_nho_04.png — Khóa chiều cao 100 cm",
        createdAt: "2026-11-01T17:31:30.000Z",
      },
    ],
    generatedClips: [
      {
        id: "clip_ep1_c1",
        url: "/demo/scenes/canh_01.mp4",
        thumbnailUrl: "/demo/scenes/canh_01.jpg",
        episodeId: "ep_01_rang_sau",
        episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
        sceneIndex: 1,
        sceneLabel: "Cảnh 1: Sóc Bi ở nhà cây, kệ đầy hũ kẹo",
        sceneTitle: "Cảnh 1: Sóc Bi ở nhà cây, kệ đầy hũ kẹo",
        durationSec: 8.0,
        model: "google-veo-2",
        createdAt: "2026-11-01T22:41:00.000Z",
      },
    ],
    appearances: [
      {
        episodeId: "ep_01_rang_sau",
        episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
        scenes: [
          "Cảnh 1: Kệ kẹo nhà cây",
          "Cảnh 2: Ăn kẹo quên đánh răng",
          "Cảnh 3: Sáng dậy đau răng",
          "Cảnh 4: Khám Bác sĩ Koala",
          "Cảnh 5: Học chải răng",
          "Cảnh 6: Răng sáng bóng",
        ],
      },
    ],
    memory: {
      personality: "Nhanh nhẹn, lanh lợi, thân thiện, tinh nghịch, tò mò",
      catchphrases: [
        "Oa, nhiều kẹo quá! Hôm nay Bi sẽ ăn thật nhiều luôn!",
        "Cảm ơn bác sĩ! Từ nay Bi sẽ chăm sóc răng thật tốt!",
      ],
      habits: ["Thích ăn hạt dẻ và kẹo ngọt", "Luôn vẫy đuôi xù khi hào hứng"],
      pastEvents: [
        "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Ăn kẹo quên đánh răng bị sâu răng, được Bác sĩ Koala chữa và dạy đánh răng sáng tối.",
      ],
      pastEventsSummary: [
        "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Ăn kẹo quên đánh răng bị sâu răng, được Bác sĩ Koala chữa và dạy đánh răng sáng tối.",
      ],
    },
  },
  {
    id: "koala",
    projectId: "soc-nho-tv",
    name: "Bác sĩ Koala",
    role: "supporting",
    description:
      "Tròn trịa, vững chãi, hiền từ. Mặc áo blouse trắng sạch có huy hiệu chữ thập xanh lá, đeo kính tròn gọng vàng và ống nghe.",
    heightCm: 150,
    scaleRatio: 1.5,
    voiceId: "voice-koala",
    defaultTempo: 1.0,
    sampleAudioUrl: "/demo/audio/canh_01.mp3",
    promptLock:
      "a gentle elderly koala doctor, about 150cm tall (1.5x the height of Bi the squirrel), soft gray fur, large round black nose, fluffy round ears, kind small eyes behind round gold glasses, wearing a clean white doctor coat with a green cross badge, a head mirror on his forehead, a stethoscope around his neck, 3D Pixar-style soft render, soft studio lighting, plain light gray background",
    referenceImages: ["/demo/scenes/canh_04.jpg", "/demo/scenes/canh_05.jpg"],
    referenceLibrary: [
      {
        id: "ref_koala_01",
        url: "/demo/scenes/canh_04.jpg",
        angle: "Khám răng cho Sóc Bi (Tỉ lệ 150cm : 100cm)",
        isPrimary: true,
        source: "generated",
        sourceType: "generated",
        model: "gemini-2.5-flash-image",
        prompt:
          "Bác sĩ Koala 150cm khám răng cho Sóc Bi 100cm tại phòng khám rừng xanh",
        createdAt: "2026-11-01T22:37:00.000Z",
      },
      {
        id: "ref_koala_02",
        url: "/demo/scenes/canh_05.jpg",
        angle: "Hướng dẫn cầm bàn chải mẫu",
        isPrimary: false,
        source: "generated",
        sourceType: "generated",
        model: "gemini-2.5-flash-image",
        prompt:
          "Bác sĩ Koala cầm bàn chải lớn hướng dẫn Bi đánh răng đúng cách",
        createdAt: "2026-11-01T22:38:00.000Z",
      },
    ],
    generatedClips: [],
    appearances: [
      {
        episodeId: "ep_01_rang_sau",
        episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
        scenes: [
          "Cảnh 4: Khám răng tại phòng khám gốc cây",
          "Cảnh 5: Hướng dẫn đánh răng đúng cách",
        ],
      },
    ],
    memory: {
      personality: "Hiền, kiên nhẫn, ấm áp, dạy dỗ nhẹ nhàng",
      catchphrases: [
        "Cháu bị sâu răng rồi. Do ăn quá nhiều kẹo ngọt đấy.",
        "Hãy đánh răng sáng và tối, ăn ít kẹo, uống nhiều nước nhé.",
      ],
      habits: [
        "Đeo kính tròn gọng vàng",
        "Dùng mô hình răng lớn để hướng dẫn",
      ],
      pastEvents: [
        "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Khám và chữa răng sâu cho Sóc Bi.",
      ],
      pastEventsSummary: [
        "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Khám và chữa răng sâu cho Sóc Bi.",
      ],
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

const INITIAL_SCHEDULED_POSTS: ScheduledPost[] = [
  {
    id: "sched_yt_ep1",
    projectId: "soc-nho-tv",
    episodeId: "ep_01_rang_sau",
    episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    title: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    channelId: "chan_yt_1",
    channelName: "Sóc Nhỏ TV Official",
    platform: "youtube",
    scheduledAt: "Thứ Sáu · 19:00",
    scheduledDate: "2026-11-06",
    scheduledTime: "19:00",
    aspectRatio: "9:16",
    status: "pending_approval",
    manualApprovalRequired: true,
  },
  {
    id: "sched_tt_ep1",
    projectId: "soc-nho-tv",
    episodeId: "ep_01_rang_sau",
    episodeTitle: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    title: "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
    channelId: "chan_tt_1",
    channelName: "@socnhotv.official",
    platform: "tiktok",
    scheduledAt: "Thứ Sáu · 20:00",
    scheduledDate: "2026-11-06",
    scheduledTime: "20:00",
    aspectRatio: "9:16",
    status: "approved",
    manualApprovalRequired: true,
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
  private memoryScheduledPosts: Map<string, ScheduledPost> = new Map(
    INITIAL_SCHEDULED_POSTS.map((p) => [p.id, p])
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
        if (!db.objectStoreNames.contains("scheduled_posts")) {
          const store = db.createObjectStore("scheduled_posts", {
            keyPath: "id",
          });
          INITIAL_SCHEDULED_POSTS.forEach((p) => store.add(p));
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
    const list = all.filter((c) => c.projectId === projectId);
    return list.length > 0
      ? list
      : INITIAL_CHARACTERS.filter((c) => c.projectId === projectId);
  }

  async saveCharacter(character: Character): Promise<void> {
    this.memoryCharacters.set(character.id, character);
    const db = await this.getDB();
    if (db) {
      await db.put("characters", character);
    }
  }

  createCharacter(character: Character): Promise<void> {
    return this.saveCharacter(character);
  }

  async upsertCharacter(
    projectId: string,
    character: Character
  ): Promise<Character> {
    const next = { ...character, projectId };
    await this.saveCharacter(next);
    return next;
  }

  async deleteCharacter(_projectId: string, id: string): Promise<void> {
    this.memoryCharacters.delete(id);
    const db = await this.getDB();
    if (db) {
      await db.delete("characters", id);
    }
  }

  async listScheduledPosts(projectId = "soc-nho-tv"): Promise<ScheduledPost[]> {
    const db = await this.getDB();
    const all = db
      ? await db.getAll("scheduled_posts")
      : Array.from(this.memoryScheduledPosts.values());
    const list = all.filter((p) => p.projectId === projectId);
    return list.length > 0
      ? list
      : INITIAL_SCHEDULED_POSTS.filter((p) => p.projectId === projectId);
  }

  async saveScheduledPost(post: ScheduledPost): Promise<void> {
    this.memoryScheduledPosts.set(post.id, post);
    const db = await this.getDB();
    if (db) {
      await db.put("scheduled_posts", post);
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
