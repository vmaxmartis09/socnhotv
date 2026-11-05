"use client";

import { enterOnce } from "@/lib/motion";
import React, { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStudioStore } from "@/store";
import { CharactersManager } from "@/components/characters/CharactersManager";
import {
  fetchProjectLibrary,
  fetchText,
  type ProjectLibrary,
  type LibraryItem,
} from "@/lib/repositories/library";
import { Users, ScrollText, Clapperboard, Video, Images, X, Film, FolderGit2, ChevronRight, Check, Plus, Pencil, Wand2, Upload, ShieldCheck } from "@/components/ui/icons";
import { PolicyEditor } from "@/components/studio/PolicyEditor";
import { fetchProjectPolicy } from "@/lib/api/policy";
import { Markdown } from "./Markdown";
import { usePreview } from "@/lib/preview";
import { useHubScope } from "@/lib/hub";
import { ScriptComposer } from "./ScriptComposer";
import { EmptyActions } from "@/components/ui/EmptyActions";
import { createEpisodeFolder, uploadLibraryFile } from "@/lib/repositories/library";
import { getRepository } from "@/lib/repositories";
import { ProjectsTab } from "./ProjectsTab";
import { EpisodeDetail } from "./EpisodeDetail";
import { cn } from "@/lib/utils";

export type HubTab = "projects" | "characters" | "scripts" | "episodes" | "videos" | "images" | "policy";
type Tab = HubTab;

const TABS: { key: Tab; label: string; Icon: React.ComponentType<{ className?: string }> }[] = [
  { key: "projects", label: "Dự án", Icon: FolderGit2 },
  { key: "characters", label: "Nhân vật", Icon: Users },
  { key: "scripts", label: "Kịch bản", Icon: ScrollText },
  { key: "episodes", label: "Tập phim", Icon: Clapperboard },
  { key: "videos", label: "Kho video", Icon: Video },
  { key: "images", label: "Kho hình ảnh", Icon: Images },
  { key: "policy", label: "Chính sách", Icon: ShieldCheck },
];

const fade = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.18 },
};

function Empty({ text }: { text: string }) {
  return <p className="py-10 text-center text-sm text-muted-foreground">{text}</p>;
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded bg-black/60 px-1.5 py-0.5 text-[11px] font-medium text-white tnum">{children}</span>
  );
}

function MediaGrid({
  items,
  kind,
  onOpen,
  emptyNode,
}: {
  items: LibraryItem[];
  kind: "video" | "image";
  onOpen: (i: LibraryItem) => void;
  emptyNode?: React.ReactNode;
}) {
  if (items.length === 0) return <>{emptyNode ?? <Empty text="Chưa có tư liệu" />}</>;
  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {items.map((it, idx) => (
        <motion.li
          key={it.id}
          initial={enterOnce(`media:${it.id}`, { opacity: 0, scale: 0.96 })}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: Math.min(idx, 12) * 0.025, duration: 0.2 }}
          whileHover={{ y: -2 }}
          className="group relative overflow-hidden rounded-lg border border-border bg-card"
        >
          <button type="button" onClick={() => onOpen(it)} className="block w-full text-left" title={it.name}>
            {kind === "video" ? (
              <video
                src={it.url + "#t=0.1"}
                preload="metadata"
                muted
                className="aspect-[9/12] w-full bg-black object-cover"
                onMouseEnter={(e) => e.currentTarget.play().catch(() => {})}
                onMouseLeave={(e) => {
                  e.currentTarget.pause();
                  e.currentTarget.currentTime = 0.1;
                }}
              />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={it.url} alt={it.name} loading="lazy" className="aspect-[9/12] w-full bg-muted/20 object-cover object-top" />
            )}
            <div className="absolute left-1.5 top-1.5 flex gap-1">
              {it.aspect && <Badge>{it.aspect}</Badge>}
              {it.durationSec ? <Badge>{it.durationSec.toFixed(1)}s</Badge> : null}
            </div>
            <p className="truncate border-t border-border px-2 py-1.5 text-xs text-muted-foreground">{it.name}</p>
          </button>
        </motion.li>
      ))}
    </ul>
  );
}

function EpisodeForm({
  title,
  setTitle,
  onSubmit,
  onCancel,
  busy,
}: {
  title: string;
  setTitle: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <form onSubmit={onSubmit} className="flex items-center gap-2 rounded-2xl border border-dashed border-border p-3">
      <Clapperboard className="h-5 w-5 shrink-0 text-muted-foreground" />
      <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Tên tập phim" className="h-8 min-w-0 flex-1 rounded-lg border border-border bg-card px-2.5 text-sm" />
      <button type="button" title="Hủy" aria-label="Hủy" onClick={onCancel} className="flex h-8 w-8 items-center justify-center rounded-full border border-border active:scale-90"><X className="h-4 w-4" /></button>
      <button type="submit" title="Tạo" aria-label="Tạo" disabled={!title.trim() || busy} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground active:scale-90 disabled:opacity-40"><Check className="h-4 w-4" /></button>
    </form>
  );
}

export function ProjectHub({
  tab: tabProp,
  onTab,
  compact = false,
}: {
  tab?: HubTab;
  onTab?: (t: HubTab) => void;
  compact?: boolean;
} = {}) {
  const { activeProjectId: openProjectId, projects, switchProject } = useStudioStore();
  const scopeOverride = useHubScope((h) => h.projectId);
  // Panel xem theo dự án đã chọn trong tab Dự án; không chọn thì theo dự án đang mở
  const activeProjectId = scopeOverride ?? openProjectId;
  const viewing = scopeOverride !== null && scopeOverride !== openProjectId;
  const scopeProject = projects.find((p) => p.id === activeProjectId);
  const [charCount, setCharCount] = useState<number | null>(null);

  // Đổi dự án đang mở bằng nơi khác (breadcrumb...) thì panel quay về theo dự án đó
  React.useEffect(() => {
    useHubScope.getState().set(null);
  }, [openProjectId]);
  React.useEffect(() => {
    setCharCount(null);
    getRepository().listCharacters(activeProjectId).then((l) => setCharCount(l.length)).catch(() => setCharCount(0));
  }, [activeProjectId]);
  const [innerTab, setInnerTab] = useState<Tab>("projects");
  const tab = tabProp ?? innerTab;
  // Chuyển tab thì vùng xem trước mở rộng đi kèm phải tắt
  const setTab = (t: Tab) => {
    usePreview.getState().close();
    if (onTab) onTab(t);
    else setInnerTab(t);
  };
  const [lib, setLib] = useState<ProjectLibrary | null>(null);
  const [error, setError] = useState("");
  const openMedia = (kind: "video" | "image", list: LibraryItem[], item: LibraryItem) =>
    usePreview.getState().open({
      kind,
      title: kind === "video" ? "Video" : "Hình ảnh",
      items: list.map((x) => ({ url: x.url, name: x.name })),
      index: Math.max(0, list.findIndex((x) => x.id === item.id)),
    });
  const [openScript, setOpenScript] = useState<string | null>(null);
  const [scriptText, setScriptText] = useState<Record<string, string>>({});
  const [openEpisode, setOpenEpisode] = useState<string | null>(null);
  const preview = usePreview((st) => st.item);

  const mockMode = useStudioStore((st) => st.isMockMode);
  const [creatingEp, setCreatingEp] = useState(false);
  const [epTitle, setEpTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const mediaInput = React.useRef<HTMLInputElement>(null);

  const reloadLib = () => fetchProjectLibrary(activeProjectId).then(setLib).catch((e) => setError(String(e.message ?? e)));

  const openComposer = (ai: boolean) =>
    usePreview.getState().open({
      kind: "custom",
      title: "Kịch bản mới",
      render: (close) => (
        <ScriptComposer
          key={String(ai)}
          projectId={activeProjectId}
          episodes={lib?.episodes ?? []}
          mockMode={mockMode}
          startWithAi={ai}
          onSaved={reloadLib}
          onClose={close}
        />
      ),
    });

  const submitEpisode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!epTitle.trim() || busy) return;
    setBusy(true);
    try {
      await createEpisodeFolder(activeProjectId, epTitle.trim());
      setEpTitle("");
      setCreatingEp(false);
      await reloadLib();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
    }
  };

  const onPickMedia = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    try {
      for (const f of Array.from(files)) await uploadLibraryFile(activeProjectId, f);
      await reloadLib();
    } catch (err) {
      setError(String((err as Error).message ?? err));
    } finally {
      setBusy(false);
      if (mediaInput.current) mediaInput.current.value = "";
    }
  };

  // Mở thẳng một tập khi được bấm từ chi tiết dự án
  const pendingFocus = useHubScope((h) => h.pendingFocus);
  useEffect(() => {
    if (!pendingFocus || tab !== "episodes" || !lib?.episodes.some((e) => e.id === pendingFocus)) return;
    setOpenEpisode(pendingFocus);
    useHubScope.getState().clearFocus();
  }, [pendingFocus, tab, lib]);

  // Việc được yêu cầu từ nơi khác (gợi ý ở dự án trống) khi tab đích mở
  const pendingAction = useHubScope((h) => h.pendingAction);
  useEffect(() => {
    if (pendingAction === "compose-script" && tab === "scripts" && lib) {
      useHubScope.getState().clearAction();
      openComposer(false);
    } else if (pendingAction === "create-episode" && tab === "episodes") {
      useHubScope.getState().clearAction();
      setCreatingEp(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingAction, tab, lib]);

  useEffect(() => {
    setError("");
    fetchProjectLibrary(activeProjectId).then(setLib).catch((e) => setError(String(e.message ?? e)));
  }, [activeProjectId]);

  // Số quy tắc chính sách đang bật của dự án đang xem
  const [policyRules, setPolicyRules] = useState<number | null>(null);
  useEffect(() => {
    let alive = true;
    setPolicyRules(null);
    fetchProjectPolicy(activeProjectId).then((p) => alive && setPolicyRules(p ? p.rules.filter((r) => r.enabled).length : 0));
    return () => {
      alive = false;
    };
  }, [activeProjectId, tab]);

  const count = (t: Tab) =>
    t === "policy" ? policyRules ?? 0 : t === "projects" ? projects.length : t === "characters" ? charCount ?? 0 : !lib ? 0 : t === "scripts" ? lib.scripts.length : t === "episodes" ? lib.episodes.length : t === "videos" ? lib.videos.length : t === "images" ? lib.images.length : 0;

  return (
    <div className={cn("space-y-3", compact && "p-2.5")}>
      <div role="tablist" className={cn("no-scrollbar sticky top-0 z-20 flex justify-start gap-1 overflow-x-auto overflow-y-hidden border-b border-border bg-card", compact && "-mx-2.5 -mt-2.5 px-2.5 pt-2.5")}>
        {TABS.map(({ key, label, Icon }) => {
          const active = tab === key;
          const empty = !!lib && key !== "characters" && key !== "projects" && count(key) === 0;
          return (
            <button
              key={key}
              role="tab"
              aria-selected={active}
              title={empty ? `${label} — trống, bấm để tạo` : key === "projects" ? "Dự án — nhấn đúp để về danh sách" : label}
              onClick={() => setTab(key)}
              onDoubleClick={key === "projects" ? () => useHubScope.getState().setDetail(null) : undefined}
              className={cn(
                "relative flex items-center gap-1.5 whitespace-nowrap px-3 py-2.5 text-[13px] font-medium transition-colors",
                empty ? "opacity-50 hover:opacity-100" : active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
                            {(key === "characters" ? charCount !== null : key === "policy" ? policyRules !== null : key === "projects" || lib) && <span className="text-xs text-muted-foreground tnum">{count(key)}</span>}
              {active && <motion.span layoutId="hub-tab" className="absolute inset-x-1 -bottom-px h-0.5 rounded bg-foreground" />}
            </button>
          );
        })}
        {/* Dự án đang xem: chấm xanh = đang mở trong Studio, nét đứt = chỉ đang xem */}
        <span
          title={viewing ? `Đang xem ${scopeProject?.name ?? activeProjectId} (chưa phải dự án đang mở)` : `${scopeProject?.name ?? activeProjectId} — đang mở trong Studio`}
          className={cn(
            "my-1.5 ml-auto flex max-w-[170px] shrink-0 items-center gap-1.5 rounded-full border px-2.5 text-xs",
            viewing ? "border-dashed border-border text-foreground" : "border-transparent bg-muted/50 text-muted-foreground"
          )}
        >
          <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", viewing ? "bg-brand" : "bg-semantic-success")} />
          <span className="truncate">{scopeProject?.name ?? activeProjectId}</span>
          {viewing && tab !== "projects" && (
            <button type="button" title="Đặt làm dự án đang mở" aria-label="Đặt làm dự án đang mở" onClick={() => { useHubScope.getState().set(null); switchProject(activeProjectId); }} className="-mr-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full hover:bg-accent active:scale-90">
              <Check className="h-3 w-3" />
            </button>
          )}
        </span>
      </div>

      {error && tab !== "characters" && (
        <p role="alert" className="rounded-md border border-border bg-muted/40 px-3 py-2 text-[13px] text-semantic-danger">
          Core không phản hồi: {error}
        </p>
      )}

      <div key={tab}>
          {tab === "characters" && <CharactersManager compact={compact} projectId={activeProjectId} />}

          {tab === "policy" && (
            <div className="space-y-3 pb-4">
              <p className="text-[13px] leading-relaxed text-muted-foreground">
                Chính sách nội dung của <b className="text-foreground">{scopeProject?.name ?? activeProjectId}</b>: áp dụng cho cả dự án, node Kiểm tra chất lượng luôn đối chiếu lời thoại, caption, kịch bản và prompt.
              </p>
              <PolicyEditor projectId={activeProjectId} />
            </div>
          )}

          {tab === "projects" && <ProjectsTab />}

          {tab === "scripts" &&
            (openScript && lib?.scripts.find((x) => x.id === openScript) ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <button type="button" title="Quay lại" aria-label="Quay lại" onClick={() => setOpenScript(null)} className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-transform hover:text-foreground active:scale-90">
                    <ChevronRight className="h-4 w-4 rotate-180" />
                  </button>
                  <ScrollText className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate text-sm font-semibold">{openScript}</span>
                </div>
                <article className="rounded-xl border border-border bg-card p-5">
                  <Markdown>{scriptText[openScript] ?? lib.scripts.find((x) => x.id === openScript)!.preview}</Markdown>
                </article>
              </div>
            ) : lib?.scripts.length ? (
              <div className="space-y-2">
                <div className="flex justify-end">
                  <button type="button" title="Kịch bản mới" aria-label="Kịch bản mới" onClick={() => openComposer(false)} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90"><Plus className="h-4 w-4" /></button>
                </div>
              <ul className="space-y-2">
                {lib.scripts.map((s, i) => {
                  const isSelected = preview?.kind === "markdown" && (preview.url === s.url || preview.title === s.name);
                  return (
                    <motion.li key={s.id} initial={enterOnce(`script:${s.id}`, { opacity: 0, y: 6 })} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }} whileHover={{ y: -1 }}>
                      <button
                        type="button"
                        className={cn(
                          "flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-all",
                          isSelected
                            ? "border-primary bg-primary/10 shadow-sm ring-2 ring-primary/40"
                            : "border-border bg-card hover:bg-muted/30 hover:border-foreground/30"
                        )}
                        title="Click để xem trước · nhấn đúp để đọc đầy đủ"
                        onClick={() => usePreview.getState().open({ kind: "markdown", title: s.name, url: s.url })}
                        onDoubleClick={() => {
                          usePreview.getState().close();
                          setOpenScript(s.id);
                          if (!scriptText[s.id]) fetchText(s.url).then((t) => setScriptText((m) => ({ ...m, [s.id]: t }))).catch(() => {});
                        }}
                      >
                        <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors", isSelected ? "bg-primary text-primary-foreground" : "bg-accent text-foreground")}>
                          <ScrollText className="h-4 w-4" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className={cn("block text-sm font-semibold transition-colors", isSelected ? "text-primary font-bold" : "text-foreground")}>
                            {s.name.replace(/\.md$/, "")}
                          </span>
                          <span className="block text-xs text-muted-foreground">{s.episodeId}</span>
                          <span className="mt-1 line-clamp-2 block text-[13px] text-muted-foreground">{s.preview.replace(/[#*>`|-]/g, " ")}</span>
                        </span>
                      </button>
                    </motion.li>
                  );
                })}
              </ul>
              </div>
            ) : (
              <EmptyActions
                items={[
                  { key: "manual", icons: [Pencil], title: "Viết kịch bản", hint: "Tự soạn Markdown rồi lưu vào một tập", onClick: () => openComposer(false) },
                  { key: "ai", icons: [Wand2], title: "AI viết kịch bản", hint: "Mô tả ý tưởng, AI dựng bảng cảnh và lời thoại", onClick: () => openComposer(true) },
                ]}
              />
            ))}

          {tab === "episodes" &&
            (openEpisode && lib?.episodes.find((e) => e.id === openEpisode) ? (
              <EpisodeDetail episode={lib.episodes.find((e) => e.id === openEpisode)!} lib={lib} onBack={() => setOpenEpisode(null)} />
            ) : lib?.episodes.length ? (
              <div className="space-y-3">
                <div className="flex justify-end">
                  <button type="button" title="Tạo tập phim" aria-label="Tạo tập phim" onClick={() => setCreatingEp((v) => !v)} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90"><Plus className={cn("h-4 w-4 transition-transform", creatingEp && "rotate-45")} /></button>
                </div>
                {creatingEp && <EpisodeForm title={epTitle} setTitle={setEpTitle} onSubmit={submitEpisode} onCancel={() => setCreatingEp(false)} busy={busy} />}
              <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {lib.episodes.map((e) => {
                  const cover = lib.images.find((im) => im.episodeId === e.id);
                  return (
                    <motion.li key={e.id} whileHover={{ y: -2 }}>
                      <button type="button" onClick={() => setOpenEpisode(e.id)} className="block w-full overflow-hidden rounded-xl border border-border bg-card text-left transition-colors hover:bg-muted/30">
                        {cover ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={cover.url} alt="" loading="lazy" className="h-36 w-full object-cover object-top" />
                        ) : (
                          <div className="flex h-36 items-center justify-center bg-accent"><Film className="h-8 w-8 text-muted-foreground" /></div>
                        )}
                        <div className="p-3">
                          <p className="text-sm font-semibold text-foreground">{e.title}</p>
                          <p className="text-xs text-muted-foreground">{e.id}</p>
                          <dl className="mt-2 flex gap-4 text-[13px] text-muted-foreground tnum">
                            <span title="Kịch bản" className="flex items-center gap-1"><ScrollText className="h-3.5 w-3.5" />{e.scriptCount}</span>
                            <span title="Video" className="flex items-center gap-1"><Video className="h-3.5 w-3.5" />{e.videoCount}</span>
                            <span title="Hình ảnh" className="flex items-center gap-1"><Images className="h-3.5 w-3.5" />{e.imageCount}</span>
                          </dl>
                        </div>
                      </button>
                    </motion.li>
                  );
                })}
              </ul>
              </div>
            ) : (
              <>
                {creatingEp ? null : (
                  <EmptyActions items={[{ key: "ep", icons: [Clapperboard], title: "Tạo tập phim", hint: "Tạo thư mục tập mới để chứa kịch bản, video và hình ảnh", onClick: () => setCreatingEp(true) }]} />
                )}
                {creatingEp && <EpisodeForm title={epTitle} setTitle={setEpTitle} onSubmit={submitEpisode} onCancel={() => setCreatingEp(false)} busy={busy} />}
              </>
            ))}

          {(tab === "videos" || tab === "images") && (() => {
            const kind = tab === "videos" ? "video" : "image";
            const list = (tab === "videos" ? lib?.videos : lib?.images) ?? [];
            const label = kind === "video" ? "video" : "hình ảnh";
            return (
              <div className="space-y-3">
                <input ref={mediaInput} type="file" hidden multiple accept={kind === "video" ? "video/mp4,video/webm,video/quicktime" : "image/png,image/jpeg,image/webp"} onChange={(e) => onPickMedia(e.target.files)} />
                {list.length > 0 && (
                  <div className="flex justify-end">
                    <button type="button" title={`Tải ${label} lên`} aria-label={`Tải ${label} lên`} disabled={busy} onClick={() => mediaInput.current?.click()} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90 disabled:opacity-50"><Upload className="h-4 w-4" /></button>
                  </div>
                )}
                <MediaGrid
                  items={list}
                  kind={kind}
                  onOpen={(i) => openMedia(kind, list, i)}
                  emptyNode={
                    <EmptyActions
                      items={[
                        { key: "upload", icons: [kind === "video" ? Video : Images], title: `Tải ${label} lên`, hint: kind === "video" ? "mp4 / webm / mov" : "png / jpg / webp", onClick: () => mediaInput.current?.click() },
                      ]}
                    />
                  }
                />
              </div>
            );
          })()}
        </div>

    </div>
  );
}
