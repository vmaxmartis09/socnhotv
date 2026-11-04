"use client";

import { enterOnce } from "@/lib/motion";
import React from "react";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "framer-motion";
import { useStudioStore } from "@/store";
import { cn } from "@/lib/utils";
import { Link } from "@/i18n/routing";
import {
  House,
  FolderGit2,
  Film,
  Plus,
  Check,
  ChevronDown,
  Sparkles,
} from "@/components/ui/icons";
import { VoiceCloneModal } from "@/components/voice/VoiceCloneModal";

/** Breadcrumb nổi trong Studio: Sảnh › dự án › tập. Chọn dự án thì canvas chuyển theo. */
export function StudioBreadcrumb() {
  const t = useTranslations("leftRail");
  const c = useTranslations("canvas");
  const {
    activeProjectId,
    projects,
    episodes,
    activeEpisodeId,
    saveState,
    selectEpisode,
    createEpisode,
    switchProject,
  } = useStudioStore();

  const [menu, setMenu] = React.useState<"project" | "episode" | null>(null);
  const [newTitle, setNewTitle] = React.useState("");
  const [voiceCloneOpen, setVoiceCloneOpen] = React.useState(false);
  const barRef = React.useRef<HTMLDivElement>(null);

  const project = projects.find((p) => p.id === activeProjectId);
  const episode = episodes.find((ep) => ep.id === activeEpisodeId);
  const saveText =
    saveState === "saving" ? c("saveSaving") : saveState === "unsaved" ? c("saveUnsaved") : c("saveSaved");

  React.useEffect(() => {
    if (!menu) return;
    const onDown = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) setMenu(null);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [menu]);

  const pill = (
    id: "project" | "episode",
    icon: React.ReactNode,
    label: string,
    title: string
  ) => (
    <button
      type="button"
      title={title}
      aria-label={title}
      aria-expanded={menu === id}
      onClick={() => setMenu((m) => (m === id ? null : id))}
      className={cn(
        "flex h-8 max-w-[220px] items-center gap-1.5 rounded-full border px-2.5 text-[13px] transition-colors active:scale-95",
        menu === id ? "border-foreground bg-accent" : "border-transparent hover:bg-accent"
      )}
    >
      <span className="text-muted-foreground">{icon}</span>
      <span className="truncate font-medium text-foreground">{label}</span>
      <ChevronDown className={cn("h-3 w-3 shrink-0 text-muted-foreground transition-transform", menu === id && "rotate-180")} />
    </button>
  );

  const popover = "absolute left-0 top-10 z-50 w-64 rounded-xl border border-border bg-popover p-1 text-popover-foreground";
  const motionProps = {
    initial: { opacity: 0, y: -4 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -4 },
    transition: { duration: 0.12 },
  };

  return (
    <motion.div
      ref={barRef}
      initial={enterOnce("breadcrumb", { opacity: 0, y: -8 })}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-auto absolute left-3 top-3 z-30 flex max-w-[calc(100%-1.5rem)] items-center gap-0.5 rounded-full border border-border bg-card/90 p-1 pr-2.5 backdrop-blur transform-gpu select-none"
    >
      {/* Về Sảnh (danh sách dự án + tiến trình) */}
      <Link href="/" title="Sảnh" aria-label="Sảnh" className="flex h-8 w-8 items-center justify-center rounded-full bg-foreground text-background transition-transform active:scale-90">
        <House className="h-3.5 w-3.5" />
      </Link>

      <span className="px-0.5 text-muted-foreground" aria-hidden="true">/</span>

      <div className="relative">
        {pill("project", <FolderGit2 className="h-3.5 w-3.5" />, project?.name || "—", t("projectLabel"))}
        <AnimatePresence>
          {menu === "project" && (
            <motion.ul {...motionProps} className={popover}>
              {projects.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => {
                      switchProject(p.id);
                      setMenu(null);
                    }}
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] hover:bg-accent"
                  >
                    <span className="min-w-0 flex-1 truncate">{p.name}</span>
                    {p.id === activeProjectId && <Check className="h-3.5 w-3.5 text-brand" />}
                  </button>
                </li>
              ))}
            </motion.ul>
          )}
        </AnimatePresence>
      </div>

      <span className="px-0.5 text-muted-foreground" aria-hidden="true">/</span>

      <div className="relative min-w-0">
        {pill("episode", <Film className="h-3.5 w-3.5" />, episode?.title || "—", t("episodesLabel"))}
        <AnimatePresence>
          {menu === "episode" && (
            <motion.div {...motionProps} className={cn(popover, "w-72")}>
              <ul className="no-scrollbar max-h-64 overflow-y-auto">
                {episodes.map((ep) => (
                  <li key={ep.id}>
                    <button
                      type="button"
                      onClick={() => {
                        selectEpisode(ep.id);
                        setMenu(null);
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] hover:bg-accent"
                    >
                      <span className="min-w-0 flex-1 truncate">{ep.title}</span>
                      {ep.id === activeEpisodeId && <Check className="h-3.5 w-3.5 text-brand" />}
                    </button>
                  </li>
                ))}
              </ul>
              <form
                className="mt-1 flex gap-1 border-t border-border p-1 pt-1.5"
                onSubmit={(e) => {
                  e.preventDefault();
                  createEpisode(newTitle.trim() || t("newEpisodeDefault"));
                  setNewTitle("");
                  setMenu(null);
                }}
              >
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder={t("newEpisodeDefault")}
                  className="h-7 min-w-0 flex-1 rounded-md border border-border bg-background px-2 text-xs"
                />
                <button type="submit" title={t("newEpisode")} aria-label={t("newEpisode")} className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground active:scale-90">
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <button
        type="button"
        title="Nhân bản giọng nói OmniVoice"
        onClick={() => setVoiceCloneOpen(true)}
        className="flex h-8 items-center gap-1.5 rounded-full border border-brand/40 bg-brand/10 px-2.5 text-xs font-medium text-brand hover:bg-brand/20 transition-all active:scale-95 shadow-2xs"
      >
        <Sparkles className="h-3.5 w-3.5 text-brand" />
        <span className="hidden sm:inline">Clone Giọng</span>
      </button>

      <span
        title={saveText}
        className={cn(
          "ml-1 h-2 w-2 shrink-0 rounded-full",
          saveState === "unsaved" ? "bg-brand" : saveState === "saving" ? "animate-pulse bg-semantic-warning" : "bg-semantic-success"
        )}
      />

      <VoiceCloneModal
        isOpen={voiceCloneOpen}
        onClose={() => setVoiceCloneOpen(false)}
        projectId={activeProjectId}
      />
    </motion.div>
  );
}
