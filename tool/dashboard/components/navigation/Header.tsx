"use client";

import React, { useEffect } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useStudioStore } from "@/store";
import { getRepository } from "@/lib/repositories";
import { checkCoreHealth, fetchNodeTypes } from "@/lib/core-api";
import { StatusIsland } from "@/components/ui/StatusIsland";
import { useTheme } from "@/components/theme/ThemeProvider";
import { usePathname, useRouter } from "@/i18n/routing";
import { cn } from "@/lib/utils";
import {
  MorphIcon,
  SunNode,
  MoonNode,
  LaptopNode,
  PanelRightClose,
  PanelRightOpen,
} from "@/components/ui/icons";
import { Mark } from "@/components/brand/Mark";

export function Header() {
  const c = useTranslations("canvas");
  const r = useTranslations("rightPanel");
  const locale = useLocale() as "vi" | "en";
  const { theme, setTheme, resolvedTheme } = useTheme();
  const {
    activeProjectId,
    projects,
    setProjects,
    setCharacters,
    setChannels,
    setScheduledPosts,
    episodes,
    activeEpisodeId,
    saveState,
    aspectRatio,
    setAspectRatio,
    rightPanelCollapsed,
    toggleRightPanel,
    setNodeCatalog,
    setCoreHealth,
  } = useStudioStore();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    let active = true;
    async function bootstrapWorkspace() {
      const repo = getRepository();
      const [projs, chars, chans, posts, health, catalog] = await Promise.all([
        repo.listProjects(),
        repo.listCharacters(activeProjectId),
        repo.listChannels(activeProjectId),
        repo.listScheduledPosts(activeProjectId),
        checkCoreHealth(),
        fetchNodeTypes(),
      ]);
      if (!active) return;
      setProjects(projs);
      setCharacters(chars);
      setChannels(chans);
      setScheduledPosts(posts);
      setCoreHealth({ ...health, checkedAt: new Date().toISOString() });
      setNodeCatalog(catalog.definitions, catalog.fromCore);
    }
    bootstrapWorkspace();
    return () => {
      active = false;
    };
  }, [
    activeProjectId,
    setProjects,
    setCharacters,
    setChannels,
    setScheduledPosts,
    setCoreHealth,
    setNodeCatalog,
  ]);

  // Keyboard shortcut Ctrl+B to toggle right panel
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggleRightPanel();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleRightPanel]);

  const project = projects.find((p) => p.id === activeProjectId);
  const episode = episodes.find((ep) => ep.id === activeEpisodeId);

  const toggleTheme = () =>
    setTheme(
      theme === "light" ? "dark" : theme === "dark" ? "system" : "light"
    );
  const switchLocale = (newLocale: "vi" | "en") =>
    router.replace(pathname, { locale: newLocale });

  const themeIconNode =
    theme === "system"
      ? LaptopNode
      : resolvedTheme === "dark"
      ? MoonNode
      : SunNode;

  const saveText =
    saveState === "saving"
      ? c("saveSaving")
      : saveState === "unsaved"
      ? c("saveUnsaved")
      : c("saveSaved");

  return (
    <header className="flex h-11 shrink-0 items-center justify-between gap-3 bg-background px-3 md:pl-1 md:pr-2.5 select-none">
      {/* Breadcrumb: project / active episode + text save state */}
      <div className="flex min-w-0 items-center gap-2 text-xs sm:text-sm">
        <Mark className="h-5 w-5 md:hidden shrink-0" />
        <span className="truncate text-muted-foreground">
          {project?.name || "Sóc Nhỏ TV"}
        </span>
        <span className="text-muted-foreground" aria-hidden="true">
          /
        </span>
        <span className="truncate font-medium text-foreground">
          {episode?.title || "Tập 1"}
        </span>
        <span
          className={cn(
            "ml-1 rounded border border-border bg-card px-1.5 py-0.5 text-[11px] tnum",
            saveState === "unsaved"
              ? "text-brand"
              : "text-muted-foreground"
          )}
        >
          {saveText}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <StatusIsland className="hidden lg:flex" />

        {/* Aspect ratio selector */}
        <label className="hidden sm:flex items-center">
          <span className="sr-only">Aspect Ratio</span>
          <select
            value={aspectRatio}
            onChange={(e) =>
              setAspectRatio(
                e.target.value as "9:16" | "16:9" | "1:1" | "4:5"
              )
            }
            className="h-7 rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
          >
            <option value="9:16">9:16</option>
            <option value="16:9">16:9</option>
            <option value="1:1">1:1</option>
            <option value="4:5">4:5</option>
          </select>
        </label>

        {/* Language toggle */}
        <div
          className="hidden sm:flex items-center rounded-md border border-border bg-card text-xs"
          role="group"
          aria-label="Language"
        >
          {(["vi", "en"] as const).map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => switchLocale(l)}
              className={cn(
                "h-7 px-2 transition-colors first:rounded-l-md last:rounded-r-md",
                locale === l
                  ? "bg-accent font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {l === "vi" ? "VI" : "EN"}
            </button>
          ))}
        </div>

        {/* Theme toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        >
          <MorphIcon
            icon={themeIconNode}
            className="h-3.5 w-3.5"
            strokeWidth={1.5}
            spring="snappy"
          />
        </button>

        {/* Right panel collapse/expand toggle */}
        <button
          type="button"
          onClick={toggleRightPanel}
          title={rightPanelCollapsed ? r("expand") : r("collapse")}
          aria-label={rightPanelCollapsed ? r("expand") : r("collapse")}
          className="hidden md:flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        >
          {rightPanelCollapsed ? (
            <PanelRightOpen className="h-3.5 w-3.5" />
          ) : (
            <PanelRightClose className="h-3.5 w-3.5" />
          )}
        </button>
      </div>
    </header>
  );
}
