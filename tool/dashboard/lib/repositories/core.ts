import type {
  IRepository,
  Project,
  Channel,
  Character,
  ScheduledPost,
  Job,
  WorkspaceConfig,
} from "./types";
import { LocalRepository } from "./local";

export const CORE_URL = (
  process.env.NEXT_PUBLIC_CORE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class CoreUnavailableError extends Error {
  constructor(detail: string) {
    super(`Core không phản hồi: ${detail}`);
    this.name = "CoreUnavailableError";
  }
}

async function core<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${CORE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch (e) {
    throw new CoreUnavailableError(e instanceof Error ? e.message : String(e));
  }
  if (!res.ok) throw new Error(`Core ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

const toAbsUrl = (u?: string): string | undefined => {
  if (!u) return u;
  if (u.startsWith("/data/") || u.startsWith("/projects/")) return CORE_URL + u;
  return u;
};

const normalizeCharacter = (c: Character): Character => {
  const pastEvents =
    c.memory?.pastEvents || c.memory?.pastEventsSummary || [];
  return {
    ...c,
    sampleAudioUrl: toAbsUrl(c.sampleAudioUrl) || "/demo/audio/soc-nho_sample.mp3",
    voiceFiles: c.voiceFiles?.map((f) => ({
      ...f,
      url: toAbsUrl(f.url) || f.url,
    })),
    referenceImages: (c.referenceImages || []).map((u) => toAbsUrl(u) || u),
    referenceLibrary: c.referenceLibrary?.map((item) => ({
      ...item,
      url: toAbsUrl(item.url) || item.url,
      source: item.source || item.sourceType || "upload",
      sourceType: item.sourceType || item.source || "upload",
    })),
    generatedClips: c.generatedClips?.map((clip) => ({
      ...clip,
      url: toAbsUrl(clip.url) || clip.url,
      thumbnailUrl: toAbsUrl(clip.thumbnailUrl),
      sceneLabel: clip.sceneLabel || clip.sceneTitle || "Cảnh 1",
      sceneTitle: clip.sceneTitle || clip.sceneLabel || "Cảnh 1",
    })),
    memory: {
      personality: c.memory?.personality || "",
      catchphrases: c.memory?.catchphrases || [],
      habits: c.memory?.habits || [],
      pastEvents,
      pastEventsSummary: pastEvents,
    },
  };
};

export class CoreRepository implements IRepository {
  private local = new LocalRepository();

  getWorkspaceConfig(): Promise<WorkspaceConfig> {
    return this.local.getWorkspaceConfig();
  }
  saveWorkspaceConfig(config: Partial<WorkspaceConfig>): Promise<void> {
    return this.local.saveWorkspaceConfig(config);
  }

  async listProjects(): Promise<Project[]> {
    try {
      return await core<Project[]>("/data/projects");
    } catch {
      return this.local.listProjects();
    }
  }
  async getProject(id: string): Promise<Project | null> {
    try {
      return await core<Project>(`/data/projects/${id}`);
    } catch (e) {
      if (e instanceof Error && e.message.startsWith("Core 404")) return null;
      return this.local.getProject(id);
    }
  }
  async saveProject(project: Project): Promise<void> {
    try {
      await core(`/data/projects/${project.id}`, {
        method: "PUT",
        body: JSON.stringify(project),
      });
    } catch {
      await this.local.saveProject(project);
    }
  }
  async deleteProject(id: string): Promise<void> {
    return this.local.deleteProject(id);
  }

  async listChannels(projectId = "soc-nho-tv"): Promise<Channel[]> {
    try {
      const items = await core<Channel[]>(
        `/data/projects/${projectId}/channels`
      );
      return items.length > 0 ? items : this.local.listChannels();
    } catch {
      return this.local.listChannels();
    }
  }
  async saveChannel(channel: Channel, projectId = "soc-nho-tv"): Promise<void> {
    try {
      const all = await this.listChannels(projectId);
      const next = all.some((c) => c.id === channel.id)
        ? all.map((c) => (c.id === channel.id ? channel : c))
        : [...all, channel];
      await core(`/data/projects/${projectId}/channels`, {
        method: "PUT",
        body: JSON.stringify(next),
      });
    } catch {
      await this.local.saveChannel(channel);
    }
  }

  async listCharacters(projectId: string): Promise<Character[]> {
    try {
      const list = await core<Character[]>(
        `/data/projects/${projectId}/characters`
      );
      if (list.length > 0) return list.map(normalizeCharacter);
      return this.local.listCharacters(projectId);
    } catch {
      return this.local.listCharacters(projectId);
    }
  }
  async saveCharacter(character: Character): Promise<void> {
    try {
      await core(
        `/data/projects/${character.projectId}/characters/${character.id}`,
        {
          method: "PUT",
          body: JSON.stringify(character),
        }
      );
    } catch {
      await this.local.saveCharacter(character);
    }
  }

  async createCharacter(character: Character): Promise<void> {
    try {
      await core(`/data/projects/${character.projectId}/characters`, {
        method: "POST",
        body: JSON.stringify(character),
      });
    } catch {
      await this.local.createCharacter(character);
    }
  }

  async upsertCharacter(
    projectId: string,
    character: Character
  ): Promise<Character> {
    const next = { ...character, projectId };
    await this.saveCharacter(next);
    return next;
  }

  async deleteCharacter(projectId: string, id: string): Promise<void> {
    try {
      await core(`/data/projects/${projectId}/characters/${id}`, {
        method: "DELETE",
      });
    } catch {
      await this.local.deleteCharacter(projectId, id);
    }
  }

  async listScheduledPosts(projectId = "soc-nho-tv"): Promise<ScheduledPost[]> {
    try {
      const data = await core<{ schedule?: ScheduledPost[] }>(
        `/projects/${projectId}/publishing`
      );
      if (data?.schedule && data.schedule.length > 0) {
        return data.schedule;
      }
    } catch {
      // fallback
    }
    return this.local.listScheduledPosts(projectId);
  }

  async saveScheduledPost(
    post: ScheduledPost,
    projectId = "soc-nho-tv"
  ): Promise<void> {
    try {
      await core(`/projects/${projectId}/publishing/schedule`, {
        method: "POST",
        body: JSON.stringify(post),
      });
    } catch {
      await this.local.saveScheduledPost(post);
    }
  }

  listJobs(projectId?: string): Promise<Job[]> {
    return this.local.listJobs(projectId);
  }
  saveJob(job: Job): Promise<void> {
    return this.local.saveJob(job);
  }
}
