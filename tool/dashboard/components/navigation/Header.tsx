"use client";

import React, { useEffect } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { getRepository } from "@/lib/repositories";
import { StatusIsland } from "@/components/ui/StatusIsland";
import { useTheme } from "@/components/theme/ThemeProvider";
import { usePathname, useRouter } from "@/i18n/routing";
import { cn } from "@/lib/utils";
import { Sun, Moon, Laptop } from "lucide-react";
import { Mark } from "@/components/brand/Mark";

const PAGE_KEYS: Record<string, string> = {
  "/": "dashboard",
  "/studio": "studio",
  "/projects": "projects",
  "/characters": "characters",
  "/publish": "publish",
  "/settings": "settings",
};

export function Header() {
  const t = useTranslations("nav");
  const { theme, setTheme, resolvedTheme } = useTheme();
  const { activeProjectId, projects, setProjects } = useStudioStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    async function loadData() {
      const repo = getRepository();
      setProjects(await repo.listProjects());
    }
    loadData();
  }, [setProjects]);

  const project = projects.find((p) => p.id === activeProjectId);
  const key = PAGE_KEYS[pathname] ?? PAGE_KEYS["/" + pathname.split("/")[1]];

  const toggleTheme = () => setTheme(theme === "light" ? "dark" : theme === "dark" ? "system" : "light");
  const switchLocale = (newLocale: "vi" | "en") => router.replace(pathname, { locale: newLocale });

  const ThemeIcon = theme === "system" ? Laptop : resolvedTheme === "dark" ? Moon : Sun;

  return (
    <header className="flex h-12 shrink-0 items-center justify-between gap-3 bg-background px-3 md:pl-1 md:pr-3">
      {/* Breadcrumb: scope, then page. On the phone the mark leads. */}
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Mark className="h-5 w-5 md:hidden" />
        <span className="truncate text-muted-foreground">{project?.name}</span>
        {key && (
          <>
            <span className="text-muted-foreground" aria-hidden="true">/</span>
            <span className="truncate font-medium text-foreground">{t(key)}</span>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        <StatusIsland className="hidden sm:flex" />

        <div className="flex items-center rounded-md border border-border bg-card text-xs" role="group" aria-label="Language">
          {(["vi", "en"] as const).map((l) => (
            <button
              key={l}
              onClick={() => switchLocale(l)}
              className={cn(
                "h-7 px-2 uppercase transition-colors first:rounded-l-md last:rounded-r-md",
                "text-muted-foreground hover:text-foreground"
              )}
            >
              {l}
            </button>
          ))}
        </div>

        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        >
          <ThemeIcon className="h-4 w-4" strokeWidth={1.5} />
        </button>
      </div>
    </header>
  );
}
