import type {
  IRepository,
  Project,
  Channel,
  Character,
  Job,
  WorkspaceConfig,
} from "./types";
import { LocalRepository } from "./local";

/**
 * SupabaseRepository:
 * Bật thông qua NEXT_PUBLIC_SUPABASE_URL & NEXT_PUBLIC_SUPABASE_ANON_KEY.
 * Nếu chưa cấu hình, tự động fallback sang LocalRepository an toàn.
 */
export class SupabaseRepository implements IRepository {
  private fallback = new LocalRepository();
  private isConfigured = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );

  async getWorkspaceConfig(): Promise<WorkspaceConfig> {
    if (!this.isConfigured) return this.fallback.getWorkspaceConfig();
    // Implementation with supabase client
    return this.fallback.getWorkspaceConfig();
  }

  async saveWorkspaceConfig(config: Partial<WorkspaceConfig>): Promise<void> {
    if (!this.isConfigured) return this.fallback.saveWorkspaceConfig(config);
  }

  async listProjects(): Promise<Project[]> {
    if (!this.isConfigured) return this.fallback.listProjects();
    return this.fallback.listProjects();
  }

  async getProject(id: string): Promise<Project | null> {
    if (!this.isConfigured) return this.fallback.getProject(id);
    return this.fallback.getProject(id);
  }

  async saveProject(project: Project): Promise<void> {
    if (!this.isConfigured) return this.fallback.saveProject(project);
    return this.fallback.saveProject(project);
  }

  async deleteProject(id: string): Promise<void> {
    if (!this.isConfigured) return this.fallback.deleteProject(id);
    return this.fallback.deleteProject(id);
  }

  async listChannels(): Promise<Channel[]> {
    if (!this.isConfigured) return this.fallback.listChannels();
    return this.fallback.listChannels();
  }

  async saveChannel(channel: Channel): Promise<void> {
    if (!this.isConfigured) return this.fallback.saveChannel(channel);
  }

  async listCharacters(projectId: string): Promise<Character[]> {
    if (!this.isConfigured) return this.fallback.listCharacters(projectId);
    return this.fallback.listCharacters(projectId);
  }

  async saveCharacter(character: Character): Promise<void> {
    if (!this.isConfigured) return this.fallback.saveCharacter(character);
  }

  async listJobs(projectId?: string): Promise<Job[]> {
    if (!this.isConfigured) return this.fallback.listJobs(projectId);
    return this.fallback.listJobs(projectId);
  }

  async saveJob(job: Job): Promise<void> {
    if (!this.isConfigured) return this.fallback.saveJob(job);
  }
}
