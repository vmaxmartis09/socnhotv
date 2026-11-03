"use client";

import React, { useEffect } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { getRepository } from "@/lib/repositories";
import { StatusIsland } from "@/components/ui/StatusIsland";
import { Button } from "@/components/ui/Button";
import { useTheme } from "@/components/theme/ThemeProvider";
import { usePathname, useRouter } from "@/i18n/routing";
import {
  Sun,
  Moon,
  Laptop,
  Languages,
  ChevronDown,
  FolderGit2,
} from "lucide-react";

export function Header() {
  const t = useTranslations();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const {
    activeProjectId,
    setActiveProjectId,
    projects,
    setProjects,
  } = useStudioStore();
  const pathname = usePathname();
  const router = useRouter();

  // Load initial projects from repository
  useEffect(() => {
    async function loadData() {
      const repo = getRepository();
      const list = await repo.listProjects();
      setProjects(list);
    }
    loadData();
  }, [setProjects]);

  const toggleTheme = () => {
    if (theme === "light") setTheme("dark");
    else if (theme === "dark") setTheme("system");
    else setTheme("light");
  };

  const switchLocale = (newLocale: "vi" | "en") => {
    router.replace(pathname, { locale: newLocale });
  };

  return (
    <header className="h-14 border-b border-border bg-card/40 backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-40">
      {/* Project Switcher */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-border bg-card shadow-subtle hover:border-primary/40 transition-colors cursor-pointer">
          <FolderGit2 className="w-3.5 h-3.5 text-primary" />
          <select
            value={activeProjectId}
            onChange={(e) => setActiveProjectId(e.target.value)}
            className="bg-transparent text-xs font-semibold text-foreground focus:outline-none cursor-pointer pr-1"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id} className="bg-card text-foreground">
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Center Island */}
      <div className="hidden sm:flex">
        <StatusIsland />
      </div>

      {/* Right Controls: Theme & Locale */}
      <div className="flex items-center gap-1.5">
        {/* Language Switcher */}
        <div className="flex items-center rounded-md border border-border bg-card p-0.5 text-xs">
          <button
            onClick={() => switchLocale("vi")}
            className="px-2 py-0.5 rounded text-[11px] font-medium transition-colors hover:text-foreground text-muted-foreground focus:text-primary active:text-primary"
          >
            VI
          </button>
          <span className="text-border">|</span>
          <button
            onClick={() => switchLocale("en")}
            className="px-2 py-0.5 rounded text-[11px] font-medium transition-colors hover:text-foreground text-muted-foreground focus:text-primary active:text-primary"
          >
            EN
          </button>
        </div>

        {/* Theme Toggle Button */}
        <Button
          variant="outline"
          size="icon"
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className="h-8 w-8"
        >
          {theme === "system" ? (
            <Laptop className="w-3.5 h-3.5 text-muted-foreground" />
          ) : resolvedTheme === "dark" ? (
            <Moon className="w-3.5 h-3.5 text-primary" />
          ) : (
            <Sun className="w-3.5 h-3.5 text-primary" />
          )}
        </Button>
      </div>
    </header>
  );
}
