import type { IRepository } from "./types";
import { LocalRepository } from "./local";
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
      repositoryInstance = new LocalRepository();
    }
  }

  return repositoryInstance;
}

export * from "./types";
export { LocalRepository } from "./local";
export { SupabaseRepository } from "./supabase";
