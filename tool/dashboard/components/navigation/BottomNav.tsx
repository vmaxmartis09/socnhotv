"use client";

import React from "react";
import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Film, FolderGit2, Users2, Settings } from "lucide-react";

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
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 h-14 border-t border-border bg-card/90 backdrop-blur-lg px-2 flex items-center justify-around select-none">
      {mobileNav.map((item) => {
        const Icon = item.icon;
        const isActive =
          pathname === item.href ||
          (item.href !== "/" && pathname.startsWith(item.href));

        if (item.isPrimary) {
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center -mt-5 w-12 h-12 rounded-full shadow-float transition-all",
                isActive
                  ? "bg-primary text-primary-foreground ring-4 ring-background"
                  : "bg-primary/90 text-primary-foreground"
              )}
              aria-label={item.label}
            >
              <Icon className="w-5 h-5" />
            </Link>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center justify-center py-1 px-2 text-[10px] font-medium transition-colors",
              isActive
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className="w-4 h-4 mb-0.5" />
            <span className="truncate max-w-[54px]">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
