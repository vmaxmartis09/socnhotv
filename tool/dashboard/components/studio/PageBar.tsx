"use client";

import React from "react";
import { motion } from "framer-motion";
import { Link } from "@/i18n/routing";
import { useStudioStore } from "@/store";
import { enterOnce } from "@/lib/motion";
import { House, FolderGit2 } from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import { allNavItems } from "@/components/navigation/nav-modules";

/**
 * Thanh sticky góc trên trái cho Sảnh/Công việc/Module, cùng kiểu breadcrumb của Studio:
 * Sảnh › dự án đang mở › các module. `page` đánh dấu trang hiện tại.
 */
export function PageBar({ page }: { page?: string }) {
  const { projects, activeProjectId } = useStudioStore();
  const project = projects.find((p) => p.id === activeProjectId);

  return (
    <motion.div
      initial={enterOnce("pagebar", { opacity: 0, y: -8 })}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-auto absolute left-3 top-3 z-30 flex items-center gap-1 rounded-full border border-border bg-card/90 p-1 pr-1.5 backdrop-blur transform-gpu select-none"
    >
      <Link
        href="/"
        title="Sảnh"
        aria-label="Sảnh"
        className={cn(
          "flex h-8 w-8 items-center justify-center rounded-full transition-transform active:scale-90",
          page === "home" ? "bg-foreground text-background" : "text-muted-foreground hover:bg-accent"
        )}
      >
        <House className="h-3.5 w-3.5" />
      </Link>
      <span className="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />

      <span
        title={`Dự án đang mở: ${project?.name ?? activeProjectId}`}
        className="flex h-8 max-w-[180px] items-center gap-1.5 pl-2 pr-2 text-[13px]"
      >
        <FolderGit2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <span className="truncate font-medium">{project?.name ?? activeProjectId}</span>
      </span>

      <span className="mx-0.5 h-4 w-px bg-border" aria-hidden="true" />

      {allNavItems.map((item) => {
        const Icon = item.icon;
        const isActive = page === item.id;
        return (
          <Link
            key={item.id}
            href={item.href}
            title={item.id}
            className={cn(
              "flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[13px] transition-transform active:scale-95",
              isActive
                ? "bg-foreground text-background font-medium"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            <span className="capitalize">{item.id}</span>
          </Link>
        );
      })}
    </motion.div>
  );
}
