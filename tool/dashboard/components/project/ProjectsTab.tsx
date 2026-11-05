"use client";

import { useShallow } from "zustand/react/shallow";
import { enterOnce } from "@/lib/motion";
import React, { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStudioStore } from "@/store";
import { getRepository } from "@/lib/repositories";
import { createProject } from "@/lib/repositories/library";
import { FolderGit2, Plus, Check, Users, Film, X, ChevronRight, Clapperboard, Video, Images, ScrollText, Workflow } from "@/components/ui/icons";
import { fetchGraphFromCore } from "@/lib/core-api";
import { fetchProjectLibrary, type ProjectLibrary } from "@/lib/repositories/library";
import type { Character } from "@/lib/repositories";
import { useRouter } from "@/i18n/routing";
import { useHubScope } from "@/lib/hub";
import { CharacterPoster } from "@/components/characters/CharacterPoster";
import { EmptyActions } from "@/components/ui/EmptyActions";
import { cn } from "@/lib/utils";

const slug = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

/** Danh sách tất cả dự án: chọn dự án đang làm việc hoặc tạo dự án mới. */
export function ProjectsTab({ canCreate = true }: { canCreate?: boolean } = {}) {
  const { projects, activeProjectId, switchProject, setProjects, setRightPanelCollapsed } = useStudioStore(
    useShallow((s) => ({
      projects: s.projects,
      activeProjectId: s.activeProjectId,
      switchProject: s.switchProject,
      setProjects: s.setProjects,
      setRightPanelCollapsed: s.setRightPanelCollapsed,
    }))
  );
  const router = useRouter();
  const detailId = useHubScope((h) => h.detailProjectId);
  const setDetailId = useHubScope.getState().setDetail;

  const join = (id: string) => {
    useHubScope.getState().set(null);
    switchProject(id);
    setRightPanelCollapsed(true);
    router.push("/studio");
  };
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = slug(name);
    if (!id) return;
    setBusy(true);
    setError("");
    try {
      await createProject({ id, name: name.trim(), description: desc.trim() });
      setProjects(await getRepository().listProjects());
      switchProject(id);
      setCreating(false);
      setName("");
      setDesc("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const detail = detailId ? projects.find((x) => x.id === detailId) : null;
  if (detail) {
    return (
      <ProjectDetail
        project={detail}
        active={detail.id === activeProjectId}
        onBack={() => setDetailId(null)}
        onFocus={() => {
          useHubScope.getState().set(null);
          switchProject(detail.id);
        }}
        onJoin={() => join(detail.id)}
        onStart={() => {
          join(detail.id);
          window.setTimeout(() => {
            const st = useStudioStore.getState();
            if (st.nodes.length === 0) st.loadCanvasTemplate("soc_nho_story");
          }, 300);
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span />
        {canCreate && (        <button
          type="button"
          title="Tạo dự án mới"
          aria-label="Tạo dự án mới"
          onClick={() => setCreating((v) => !v)}
          className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground transition-transform active:scale-90"
        >
          {creating ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        </button>
        )}
      </div>

      <AnimatePresence initial={false}>
        {creating && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            onSubmit={submit}
            className="overflow-hidden"
          >
            <div className="space-y-2 rounded-lg border border-border bg-muted/20 p-3">
              <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Tên dự án" className="h-8 w-full rounded-md border border-border bg-card px-2.5 text-sm" />
              <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Mô tả ngắn" className="h-8 w-full rounded-md border border-border bg-card px-2.5 text-sm" />
              <div className="flex items-center justify-between gap-2">
                <code className="truncate text-xs text-muted-foreground">{slug(name) || "id-du-an"}</code>
                <button type="submit" disabled={!slug(name) || busy} title="Tạo" aria-label="Tạo" className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground disabled:opacity-40 active:scale-90">
                  <Check className="h-4 w-4" />
                </button>
              </div>
              {error && <p className="text-xs text-semantic-danger">{error}</p>}
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {projects.map((p, i) => {
          const active = p.id === activeProjectId;
          const picked = p.id === activeProjectId;
          return (
            <motion.li
              key={p.id}
              initial={enterOnce(`proj:${p.id}`, { opacity: 0, y: 8 })}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              whileHover={{ y: -2 }}
            >
              <button
                type="button"
                onClick={() => {
                  setDetailId(p.id);
                  useHubScope.getState().set(p.id);
                }}
                onDoubleClick={() => join(p.id)}
                title={`${p.name} — nhấn đúp để vào`}
                className={cn(
                  "relative flex h-full w-full flex-col gap-4 rounded-2xl border p-5 text-left transition-colors",
                  picked ? "border-foreground bg-card" : "border-border bg-card hover:bg-muted/30"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent text-foreground">
                    <FolderGit2 className="h-6 w-6" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-base font-semibold text-foreground">{p.name}</p>
                    <p className="line-clamp-2 text-[13px] text-muted-foreground">{p.description || p.id}</p>
                  </div>
                </div>
                <div className="mt-auto flex items-center gap-4 text-sm text-muted-foreground tnum">
                  <span title="Nhân vật" className="flex items-center gap-1"><Users className="h-3.5 w-3.5" />{p.charactersCount}</span>
                  <span title="Tập phim" className="flex items-center gap-1"><Film className="h-3.5 w-3.5" />{p.episodesCount}</span>
                  <span className="ml-auto">{p.defaultAspectRatio}</span>
                </div>
                {active && (
                  <span className="absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Check className="h-3 w-3" />
                  </span>
                )}
              </button>
            </motion.li>
          );
        })}
      </ul>
    </div>
  );
}

/** Chi tiết một dự án: xem rồi quay lại; Focus để làm dự án hiện tại, Vào Studio để mở canvas. */
function ProjectDetail({
  project,
  active,
  onBack,
  onFocus,
  onJoin,
  onStart,
}: {
  project: import("@/lib/repositories").Project;
  active: boolean;
  onBack: () => void;
  onFocus: () => void;
  onJoin: () => void;
  /** Vào Studio của dự án này và tạo đồ thị mẫu nếu canvas còn trống */
  onStart: () => void;
}) {
  const [chars, setChars] = useState<Character[] | null>(null);
  const [lib, setLib] = useState<ProjectLibrary | null>(null);
  const st = useStudioStore.getState();
  const router = useRouter();
  const [coreSteps, setCoreSteps] = useState<number | null>(null);
  const [newFlow, setNewFlow] = useState<string | null>(null);

  // Flow của dự án: mỗi tập/đồ thị trong Studio. Dự án chưa mở lần nào thì lấy đồ thị đã lưu ở Core.
  const savedWs = st.projectWorkspaces[project.id];
  React.useEffect(() => {
    setCoreSteps(null);
    if (!active && !savedWs) fetchGraphFromCore(project.id).then((g) => setCoreSteps(g ? g.nodes.length : 0));
  }, [project.id, active, savedWs]);
  const ws = active
    ? { episodes: st.episodes, activeEpisodeId: st.activeEpisodeId, graphs: st.graphsByEpisode, nodes: st.nodes }
    : savedWs
    ? { episodes: savedWs.episodes, activeEpisodeId: savedWs.activeEpisodeId, graphs: savedWs.graphsByEpisode, nodes: savedWs.nodes }
    : null;
  const flows = ws
    ? ws.episodes.map((e) => ({
        id: e.id,
        title: e.title,
        steps: e.id === ws.activeEpisodeId ? ws.nodes.length : ws.graphs[e.id]?.nodes.length ?? e.nodeCount,
      }))
    : coreSteps
    ? [{ id: "main", title: "Flow chính", steps: coreSteps }]
    : [];

  const openFlow = (id: string) => {
    if (!active) st.switchProject(project.id);
    useHubScope.getState().set(null);
    st.setRightPanelCollapsed(true);
    router.push("/studio");
    if (id !== "main") window.setTimeout(() => useStudioStore.getState().selectEpisode(id), 250);
  };
  const createFlow = (e: React.FormEvent) => {
    e.preventDefault();
    const title = (newFlow ?? "").trim();
    if (!title) return;
    if (!active) st.switchProject(project.id);
    st.createEpisode(title);
    setNewFlow(null);
  };

  React.useEffect(() => {
    setChars(null);
    setLib(null);
    getRepository().listCharacters(project.id).then(setChars).catch(() => setChars([]));
    fetchProjectLibrary(project.id).then(setLib).catch(() => setLib(null));
  }, [project.id]);

  const counts = [
    { Icon: Users, label: "Nhân vật", n: chars?.length ?? project.charactersCount },
    { Icon: ScrollText, label: "Kịch bản", n: lib?.scripts.length ?? 0 },
    { Icon: Clapperboard, label: "Tập phim", n: lib?.episodes.length ?? project.episodesCount },
    { Icon: Video, label: "Video", n: lib?.videos.length ?? 0 },
    { Icon: Images, label: "Hình ảnh", n: lib?.images.length ?? 0 },
  ];

  return (
    <motion.div initial={enterOnce(`pd:${project.id}`, { opacity: 0, x: 16 })} animate={{ opacity: 1, x: 0 }} className="space-y-4">
      <div className="flex items-center gap-2">
        <button type="button" title="Quay lại" aria-label="Quay lại" onClick={onBack} className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-transform hover:text-foreground active:scale-90">
          <ChevronRight className="h-4 w-4 rotate-180" />
        </button>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent"><FolderGit2 className="h-4 w-4" /></span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-base font-semibold text-foreground">{project.name}</h2>
          <p className="text-xs text-muted-foreground">{project.id}</p>
        </div>
        {/* Vào Studio chỉ có ở chi tiết dự án; Focus chỉ cần khi dự án này chưa phải dự án đang mở */}
        {!active && (
          <button type="button" title="Đặt làm dự án đang mở" aria-label="Focus dự án" onClick={onFocus} className="flex h-8 w-8 items-center justify-center rounded-full border border-border transition-transform hover:bg-accent active:scale-90">
            <Check className="h-4 w-4" />
          </button>
        )}
        <button type="button" title="Vào Studio" aria-label="Vào Studio" onClick={onJoin} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform active:scale-90">
          <Film className="h-4 w-4" />
        </button>
      </div>

      {project.description && <p className="text-[13px] leading-relaxed text-muted-foreground">{project.description}</p>}

      <ul className="flex flex-wrap gap-2">
        {counts.map(({ Icon, label, n }) => (
          <li key={label} title={label} className={cn("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[13px] tnum", n ? "border-border text-foreground" : "border-dashed border-border text-muted-foreground/50")}>
            <Icon className="h-3.5 w-3.5" />
            {n}
          </li>
        ))}
        <li title="Tỉ lệ khung hình" className="rounded-full border border-border px-2.5 py-1 text-[13px] tnum">{project.defaultAspectRatio}</li>
      </ul>

      {/* Flow của dự án (mỗi tập/đồ thị): bấm để mở trong Studio */}
      <section className="space-y-2">
        <div className="flex items-center gap-2 text-[13px] font-semibold text-foreground">
          <Workflow className="h-4 w-4 text-muted-foreground" />
          <span>Flow</span>
          <span className="text-xs font-normal text-muted-foreground tnum">{flows.filter((f) => f.steps > 0).length}</span>
          <button type="button" title="Tạo flow mới" aria-label="Tạo flow mới" onClick={() => setNewFlow((v) => (v === null ? "" : null))} className="ml-auto flex h-7 w-7 items-center justify-center rounded-full border border-border transition-transform hover:bg-accent active:scale-90">
            <Plus className={cn("h-3.5 w-3.5 transition-transform", newFlow !== null && "rotate-45")} />
          </button>
        </div>
        {newFlow !== null && (
          <form onSubmit={createFlow} className="flex items-center gap-2 rounded-2xl border border-dashed border-border p-2.5">
            <Workflow className="h-4 w-4 shrink-0 text-muted-foreground" />
            <input autoFocus value={newFlow} onChange={(e) => setNewFlow(e.target.value)} placeholder="Tên flow (tập)" className="h-8 min-w-0 flex-1 rounded-lg border border-border bg-card px-2.5 text-sm" />
            <button type="submit" title="Tạo flow" aria-label="Tạo flow" disabled={!newFlow.trim()} className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground active:scale-90 disabled:opacity-40"><Check className="h-4 w-4" /></button>
          </form>
        )}
        <ul className="space-y-1.5">
          {flows.map((f) => (
            <li key={f.id}>
              <button
                type="button"
                onClick={() => openFlow(f.id)}
                title={f.steps === 0 ? `${f.title} — flow trống, bấm để mở trong Studio` : `Mở ${f.title} trong Studio`}
                className={cn("flex w-full items-center gap-3 rounded-xl border px-3 py-2 text-left text-[13px] transition-colors hover:bg-muted/30", f.steps === 0 ? "border-dashed border-border text-muted-foreground" : "border-border text-foreground")}
              >
                <Workflow className="h-4 w-4 shrink-0 text-brand" />
                <span className="min-w-0 flex-1 truncate font-medium">{f.title}</span>
                <span className="shrink-0 text-xs text-muted-foreground tnum">{f.steps} bước</span>
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              </button>
            </li>
          ))}
        </ul>
      </section>

      {chars && chars.length > 0 && (
        <ul aria-label="Nhân vật" className="no-scrollbar flex gap-3 overflow-x-auto overflow-y-hidden py-1">
          {chars.map((c) => (
            <li key={c.id} className="shrink-0">
              <CharacterPoster
                character={c}
                roleLabel={c.role === "main" ? "Nhân vật chính" : "Nhân vật phụ"}
                onClick={() => useHubScope.getState().openTab("characters", null, c.id)}
              />
            </li>
          ))}
        </ul>
      )}

      {lib && lib.episodes.length > 0 && (
        <ul className="space-y-1.5">
          {lib.episodes.map((e) => (
            <li key={e.id}>
              <button type="button" title={`Mở ${e.title}`} onClick={() => useHubScope.getState().openTab("episodes", null, e.id)} className="flex w-full items-center gap-2 rounded-xl border border-border px-3 py-2 text-left text-[13px] transition-colors hover:bg-muted/30">
                <Film className="h-4 w-4 shrink-0 text-brand" />
                <span className="min-w-0 flex-1 truncate">{e.title}</span>
                <span className="text-xs text-muted-foreground tnum">{e.videoCount}▶ · {e.imageCount}◼</span>
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Chưa có gì thì gợi ý việc cần làm: mỗi ô mở đúng chức năng tạo tương ứng */}
      <EmptyActions
        items={[
          ...(chars && chars.length === 0
            ? [{ key: "chars", icons: [Users], title: "Tạo nhân vật", hint: "Thủ công hoặc mô tả để AI dựng hồ sơ", onClick: () => useHubScope.getState().openTab("characters", "create-character") }]
            : []),
          ...(lib && lib.scripts.length === 0
            ? [{ key: "script", icons: [ScrollText], title: "Viết kịch bản", hint: "Tự viết hoặc nhờ AI dựng bảng cảnh và lời thoại", onClick: () => useHubScope.getState().openTab("scripts", "compose-script") }]
            : []),
          ...(lib && lib.episodes.length === 0
            ? [{ key: "episode", icons: [Clapperboard], title: "Tạo tập phim", hint: "Thư mục tập chứa kịch bản, video và hình ảnh", onClick: () => useHubScope.getState().openTab("episodes", "create-episode") }]
            : []),
          ...(lib && lib.videos.length === 0 && lib.images.length === 0
            ? [{ key: "media", icons: [Video, Images], title: "Tải video và hình ảnh", hint: "Đưa tư liệu có sẵn vào kho của dự án", onClick: () => useHubScope.getState().openTab("videos") }]
            : []),
          ...(lib && lib.episodes.length === 0
            ? [{ key: "studio", icons: [Film], title: "Dựng đồ thị mẫu trong Studio", hint: "Pipeline 9 bước để sinh video và hình ảnh", onClick: onStart }]
            : []),
        ]}
      />
    </motion.div>
  );
}
