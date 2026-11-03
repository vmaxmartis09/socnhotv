import type { IRepository } from "./types";
import { CoreRepository } from "./core";
import { SupabaseRepository } from "./supabase";

let repositoryInstance: IRepository | null = null;

export function getRepository(): IRepository {
  if (!repositoryInstance) {
    const useSupabase = Boolean(
      process.env.NEXT_PUBLIC_SUPABASE_URL &&
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    );

    if (useSupabase) {
      repositoryInstance = new SupabaseRepository();
    } else {
      repositoryInstance = new CoreRepository();
    }
  }

  return repositoryInstance;
}

export * from "./types";
export { LocalRepository } from "./local";
export { CoreRepository, CORE_URL, CoreUnavailableError } from "./core";
export { SupabaseRepository } from "./supabase";
