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
  Sparkles,
  Layers,
} from "lucide-react";
import { useStudioStore } from "@/store";

export function Sidebar() {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const { activeProjectId } = useStudioStore();

  const navItems = [
    { href: "/", label: t("dashboard"), icon: LayoutDashboard },
    { href: "/studio", label: t("studio"), icon: Film, highlight: true },
    { href: "/projects", label: t("projects"), icon: FolderGit2 },
    { href: "/characters", label: t("characters"), icon: Users2 },
    { href: "/publish", label: t("publish"), icon: CalendarDays },
    { href: "/settings", label: t("settings"), icon: Settings },
  ];

  return (
    <aside className="hidden md:flex flex-col w-60 shrink-0 border-r border-border bg-card/60 backdrop-blur-md h-screen sticky top-0">
      {/* Brand & Project Info */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center text-primary-foreground shadow-subtle">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-foreground leading-none">
              AI Video Studio
            </h1>
            <p className="text-[11px] text-muted-foreground mt-0.5 truncate max-w-[140px]">
              {activeProjectId}
            </p>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all duration-150 select-none",
                isActive
                  ? "bg-primary text-primary-foreground shadow-subtle"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                item.highlight &&
                  !isActive &&
                  "text-primary font-semibold hover:bg-primary/10"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-border">
        <div className="p-2.5 rounded-md bg-muted/40 border border-border/50 text-[11px] text-muted-foreground">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-foreground">Storage Engine</span>
            <span className="px-1.5 py-0.2 rounded bg-semantic-success/15 text-semantic-success text-[9px] font-semibold">
              LOCAL
            </span>
          </div>
          <p className="text-[10px] leading-relaxed">
            Dữ liệu lưu tại máy (IndexedDB), bảo mật 100%.
          </p>
        </div>
      </div>
    </aside>
  );
}
