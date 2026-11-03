"use client";

import React from "react";
import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Film, FolderGit2, Users2, Settings } from "@/components/ui/icons";

export function BottomNav() {
  const t = useTranslations("nav");
  const pathname = usePathname();

  const mobileNav = [
    { href: "/", label: t("dashboard"), icon: LayoutDashboard },
    { href: "/studio", label: t("studio"), icon: Film, isPrimary: true },
    { href: "/projects", label: t("projects"), icon: FolderGit2 },
    { href: "/characters", label: t("characters"), icon: Users2 },
    { href: "/settings", label: t("settings"), icon: Settings },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 h-14 border-t border-border bg-background px-2 flex items-center justify-around select-none">
      {mobileNav.map((item) => {
        const Icon = item.icon;
        const isActive =
          pathname === item.href ||
          (item.href !== "/" && pathname.startsWith(item.href));

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "relative flex min-w-12 flex-col items-center justify-center px-2 py-1 text-xs transition-colors",
              isActive
                ? "font-medium text-foreground after:absolute after:inset-x-3 after:-top-px after:h-0.5 after:bg-brand"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className="mb-0.5 h-4 w-4" strokeWidth={1.5} />
            <span className="truncate max-w-[64px]">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
