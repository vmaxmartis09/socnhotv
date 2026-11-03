"use client";

import React from "react";
import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Film,
  FolderGit2,
  Users2,
  CalendarDays,
  Settings,
} from "lucide-react";
import { useStudioStore } from "@/store";
import { Mark } from "@/components/brand/Mark";

export function Sidebar() {
  const t = useTranslations("nav");
  const s = useTranslations("shell");
  const pathname = usePathname();
  const { activeProjectId, setActiveProjectId, projects } = useStudioStore();

  const navItems = [
    { href: "/", label: t("dashboard"), icon: LayoutDashboard },
    { href: "/studio", label: t("studio"), icon: Film },
    { href: "/projects", label: t("projects"), icon: FolderGit2 },
    { href: "/characters", label: t("characters"), icon: Users2 },
    { href: "/publish", label: t("publish"), icon: CalendarDays },
  ];
  const settings = { href: "/settings", label: t("settings"), icon: Settings };

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(href));

  const row = (item: { href: string; label: string; icon: typeof Film }) => {
    const Icon = item.icon;
    const active = isActive(item.href);
    return (
      <Link
        key={item.href}
        href={item.href}
        aria-current={active ? "page" : undefined}
        className={cn(
          "flex h-8 items-center gap-2.5 rounded-md px-2.5 text-sm select-none transition-colors",
          active
            ? "bg-accent font-medium text-foreground"
            : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
        )}
      >
        <Icon className="h-4 w-4 shrink-0" strokeWidth={1.5} />
        <span className="truncate">{item.label}</span>
      </Link>
    );
  };

  return (
    <aside className="hidden md:flex w-[228px] shrink-0 flex-col h-dvh bg-background px-2 pt-3 pb-2">
      {/* Product mark and name */}
      <div className="flex items-center gap-2 px-2.5 pb-3">
        <Mark className="h-6 w-6" />
        <span className="text-sm font-semibold tracking-tight">AI Video Studio</span>
      </div>

      {/* Project switcher */}
      <label className="mb-3 block px-1">
        <span className="sr-only">{s("project")}</span>
        <select
          value={activeProjectId}
          onChange={(e) => setActiveProjectId(e.target.value)}
          className="h-8 w-full cursor-pointer rounded-md border border-border bg-card px-2 text-sm font-medium text-foreground"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </label>

      <nav className="flex-1 space-y-0.5 overflow-y-auto">{navItems.map(row)}</nav>

      <div className="space-y-2">
        {row(settings)}
        <p className="px-2.5 text-xs leading-snug text-muted-foreground">
          {s("storage")}
          <br />
          {s("storageNote")}
        </p>
      </div>
    </aside>
  );
}
