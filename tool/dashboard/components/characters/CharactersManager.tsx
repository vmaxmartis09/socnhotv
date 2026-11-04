"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { getRepository, type Character } from "@/lib/repositories";
import { useStudioStore } from "@/store";
import { Button } from "@/components/ui/Button";
import { Plus, Pencil, Wand2, X, ChevronRight, Sparkles } from "@/components/ui/icons";
import { AnimatePresence, motion } from "framer-motion";
import { AiLoading } from "@/components/ui/AiLoading";
import { EmptyActions } from "@/components/ui/EmptyActions";
import { useHubScope } from "@/lib/hub";
import { CharacterPoster } from "./CharacterPoster";
import { CharacterDialog } from "@/components/characters/CharacterDialog";
import { CharacterDetail } from "@/components/characters/CharacterDetail";
import { VoiceCloneModal } from "@/components/voice/VoiceCloneModal";
import {
  uploadCharacterImage,
  deleteCharacterImage,
  uploadVoiceSample,
  cloneCharacterVoice,
  generateCharacterDraft,
} from "@/lib/repositories/character-assets";
import { queueCharacterForStudio } from "@/lib/studio-bridge";
import { useRouter } from "@/i18n/routing";
import { confirm } from "@/lib/confirm";
import { usePreview } from "@/lib/preview";
import { cn } from "@/lib/utils";

function ScaleLockGraph({ characters }: { characters: Character[] }) {
  const t = useTranslations("characters");
  const tallest = Math.max(...characters.map((c) => c.heightCm), 1);
  const H = 140;

  return (
    <figure aria-label={t("scaleLock")} className="rounded-lg border border-border bg-card p-4">
      <figcaption className="text-sm font-semibold text-foreground">{t("scaleLock")}</figcaption>
      <p className="mt-0.5 text-xs text-muted-foreground">{t("scaleLockNote")}</p>
      <div className="mt-6 flex items-end justify-center gap-8 border-b border-border pb-1">
        {characters.map((c) => {
          const h = Math.round((c.heightCm / tallest) * H);
          return (
            <div key={c.id} className="flex flex-col items-center gap-1.5">
              <span className="text-xs tnum font-medium text-foreground">{t("cm", { value: c.heightCm })}</span>
              <div
                style={{ height: h }}
                className={cn("w-12 rounded-t transition-all", c.role === "main" ? "bg-brand" : "bg-brand/35")}
              />
              <span className="mt-1 text-xs font-medium text-muted-foreground">
                {c.name.replace(/\s*\(.*\)/, "").replace("Bạn ", "")}
              </span>
            </div>
          );
        })}
      </div>
    </figure>
  );
}

/** Thêm node "character" (gắn characterId) vào đồ thị Studio đang có trong store. */
function addCharacterNodeToStore(c: Character) {
  const { nodes, edges, setNodesAndEdges } = useStudioStore.getState();
  if (nodes.length === 0) return;
  const maxY = Math.max(...nodes.map((n) => n.position.y), 0);
  setNodesAndEdges(
    [
      ...nodes,
      {
        id: `node_char_${Date.now().toString(36)}`,
        type: "studioCard",
        position: { x: 40, y: maxY + 260 },
        data: { nodeType: "character", status: "idle", params: { characterId: c.id }, generations: [] },
      },
    ],
    edges
  );
}

/** Dải nhân vật dạng poster: ảnh lớn, chữ nằm trên ảnh, có nút trượt qua lại khi nhiều nhân vật. */
function CharacterStrip({
  characters,
  selectedId,
  onSelect,
  title,
  roleLabel,
  addOpen,
  onToggleAdd,
  onManual,
  onAi,
  onVoiceClone,
}: {
  characters: Character[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  title: string;
  roleLabel: (c: Character) => string;
  addOpen: boolean;
  onToggleAdd: () => void;
  onManual: () => void;
  onAi: () => void;
  onVoiceClone?: () => void;
}) {
  const ref = React.useRef<HTMLUListElement>(null);
  const [edge, setEdge] = useState({ left: false, right: false });

  const measure = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    setEdge({ left: el.scrollLeft > 4, right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
  }, []);
  useEffect(() => {
    measure();
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [measure, characters.length]);

  // Giữ nhân vật đang chọn trong tầm nhìn
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>('[aria-current="true"]')?.scrollIntoView({ inline: "nearest", block: "nearest", behavior: "smooth" });
  }, [selectedId]);

  const step = (dir: 1 | -1) => ref.current?.scrollBy({ left: dir * 300, behavior: "smooth" });

  return (
    <div className="relative">
      <ul
        ref={ref}
        onScroll={measure}
        onWheel={(e) => {
          if (ref.current && Math.abs(e.deltaY) > Math.abs(e.deltaX)) ref.current.scrollLeft += e.deltaY;
        }}
        aria-label={title}
        className="no-scrollbar flex gap-3 overflow-x-auto overflow-y-hidden py-1"
      >
        {characters.map((c) => {
          return (
            <li key={c.id} className="shrink-0">
              <CharacterPoster character={c} active={c.id === selectedId} roleLabel={roleLabel(c)} onClick={() => onSelect(c.id)} />
            </li>
          );
        })}
        <li className="shrink-0">
          {addOpen ? (
            <div className="flex h-[168px] w-[124px] flex-col items-stretch justify-center gap-1.5 rounded-2xl border-2 border-dashed border-border p-2">
              <button type="button" title="Tạo thủ công" aria-label="Tạo thủ công" onClick={onManual} className="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-xl text-[11px] text-foreground hover:bg-accent active:scale-95">
                <Pencil className="h-3.5 w-3.5" />Thủ công
              </button>
              <button type="button" title="Tạo bằng AI (mô tả bằng lời)" aria-label="Tạo bằng AI" onClick={onAi} className="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-xl bg-primary text-[11px] text-primary-foreground active:scale-95">
                <Wand2 className="h-3.5 w-3.5" />Bằng AI
              </button>
              <button type="button" title="Clone giọng để tạo nhân vật" aria-label="Clone giọng để tạo nhân vật" onClick={onVoiceClone} className="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-xl border border-brand/40 bg-brand/10 text-[11px] font-medium text-brand hover:bg-brand/20 active:scale-95">
                <Sparkles className="h-3.5 w-3.5 text-brand" />Clone Giọng
              </button>
            </div>
          ) : (
            <button type="button" title="Thêm nhân vật" aria-label="Thêm nhân vật" onClick={onToggleAdd} className="flex h-[168px] w-[124px] items-center justify-center rounded-2xl border-2 border-dashed border-border text-muted-foreground transition-colors hover:border-foreground hover:text-foreground active:scale-[0.98]">
              <Plus className="h-6 w-6" />
            </button>
          )}
        </li>
      </ul>
      {(["left", "right"] as const).map((side) =>
        edge[side] ? (
          <button
            key={side}
            type="button"
            title={side === "left" ? "Nhân vật trước" : "Nhân vật sau"}
            aria-label={side === "left" ? "Nhân vật trước" : "Nhân vật sau"}
            onClick={() => step(side === "left" ? -1 : 1)}
            className={cn("absolute top-1/2 z-10 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-border bg-card/95 text-foreground shadow-sm backdrop-blur transition-transform active:scale-90", side === "left" ? "left-1" : "right-1")}
          >
            <ChevronRight className={cn("h-4 w-4", side === "left" && "rotate-180")} />
          </button>
        ) : null
      )}
    </div>
  );
}

/** Quản lý nhân vật: danh sách + chi tiết (ảnh DNA, giọng, clip), thêm/sửa/xóa/nhân bản/đưa lên kịch bản. */
export function CharactersManager({ compact = false, projectId }: { compact?: boolean; projectId?: string } = {}) {
  const t = useTranslations("characters");
  const storeProjectId = useStudioStore((st) => st.activeProjectId);
  const activeProjectId = projectId ?? storeProjectId;
  const router = useRouter();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createMenu, setCreateMenu] = useState(false);
  const pendingAction = useHubScope((h) => h.pendingAction);
  useEffect(() => {
    if (pendingAction !== "create-character") return;
    useHubScope.getState().clearAction();
    // Chưa có nhân vật thì các ô gợi ý đã hiện sẵn; đã có thì mở menu tạo
    setCreateMenu(true);
  }, [pendingAction]);
  const pendingFocus = useHubScope((h) => h.pendingFocus);
  useEffect(() => {
    if (!pendingFocus || !characters.some((c) => c.id === pendingFocus)) return;
    setSelectedId(pendingFocus);
    useHubScope.getState().clearFocus();
  }, [pendingFocus, characters]);
  const [aiOpen, setAiOpen] = useState(false);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [voiceCloneOpen, setVoiceCloneOpen] = useState(false);
  const isMockMode = useStudioStore((s) => s.isMockMode);

  // Tạo bằng AI: dựng bản nháp từ mô tả rồi mở form để người dùng duyệt trước khi lưu
  const generateWithAi = async () => {
    if (!aiPrompt.trim() || aiBusy) return;
    setAiBusy(true);
    setNotice("");
    try {
      const { draft } = await generateCharacterDraft(activeProjectId, aiPrompt, isMockMode);
      const id = draft.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
      openForm(undefined, {
          id,
          name: draft.name,
          role: draft.role,
          heightCm: draft.heightCm,
          scaleRatio: Math.round((draft.heightCm / 100) * 100) / 100,
          description: draft.description,
          promptLock: draft.promptLock,
          memory: { personality: draft.personality, catchphrases: draft.catchphrases ?? [], habits: draft.habits ?? [], pastEventsSummary: [] },
      });
      setAiOpen(false);
      setAiPrompt("");
    } catch (e) {
      setNotice(t("error", { message: e instanceof Error ? e.message : String(e) }));
    } finally {
      setAiBusy(false);
    }
  };
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const list = await getRepository().listCharacters(activeProjectId);
    const sorted = [...list].sort((a, b) => Number(b.role === "main") - Number(a.role === "main"));
    setCharacters(sorted);
    setSelectedId((cur) => (cur && sorted.some((c) => c.id === cur) ? cur : sorted[0]?.id ?? null));
  }, [activeProjectId]);

  useEffect(() => {
    load().catch((e) => setNotice(t("error", { message: String(e.message ?? e) })));
  }, [load, t]);

  const selected = characters.find((c) => c.id === selectedId);

  async function run(action: () => Promise<void>, withBusy = false) {
    setNotice("");
    if (withBusy) setBusy(true);
    try {
      await action();
      await load();
    } catch (e) {
      setNotice(t("error", { message: e instanceof Error ? e.message : String(e) }));
    } finally {
      if (withBusy) setBusy(false);
    }
  }

  const handleSave = async (
    c: Character,
    isNew: boolean,
    pendingFiles?: File[],
    removedImageNames?: string[]
  ) => {
    const repo = getRepository();
    await (isNew ? repo.createCharacter(c) : repo.saveCharacter(c));
    if (isNew) setSelectedId(c.id);

    // Tải các ảnh DNA mới lên động cơ Core nếu có
    if (pendingFiles && pendingFiles.length > 0) {
      for (const f of pendingFiles) {
        try {
          await uploadCharacterImage(activeProjectId, c.id, f);
        } catch (err) {
          console.warn("Upload DNA image to Core skipped/failed:", err);
        }
      }
    }

    // Xóa các ảnh DNA đã chọn gỡ khỏi Core nếu có
    if (removedImageNames && removedImageNames.length > 0) {
      for (const name of removedImageNames) {
        try {
          await deleteCharacterImage(activeProjectId, c.id, name);
        } catch (err) {
          console.warn("Delete DNA image from Core skipped/failed:", err);
        }
      }
    }

    await load();
  };

  /** Form tạo/sửa mở rộng sang trái (quy tắc: không dùng modal khi mở rộng được) */
  const openForm = (initial?: Character, prefill?: Partial<Character>) =>
    usePreview.getState().open({
      kind: "custom",
      title: initial ? t("editTitle") : t("createTitle"),
      render: (close) => (
        <CharacterDialog
          inline
          key={initial?.id ?? prefill?.id ?? "new"}
          initial={initial}
          prefill={prefill}
          projectId={activeProjectId}
          onSave={handleSave}
          onClose={close}
        />
      ),
    });

  const patch = (c: Character, fields: Record<string, unknown>) =>
    getRepository().saveCharacter({ id: c.id, projectId: c.projectId, ...fields } as unknown as Character);

  const handleDuplicate = async (c: Character) => {
    const ok = await confirm({ tone: "info", title: t("duplicate") + ": " + c.name, message: t("copySuffix").trim() });
    if (!ok) return;
    await run(async () => {
      let id = `${c.id}_copy`;
      for (let n = 2; characters.some((x) => x.id === id); n++) id = `${c.id}_copy${n}`;
      await getRepository().createCharacter({
        ...c,
        id,
        name: c.name + t("copySuffix"),
        role: "supporting",
        referenceImages: [],
      });
      setSelectedId(id);
    });
  };

  const handleDelete = async (c: Character) => {
    const ok = await confirm({
      tone: "danger",
      title: t("delete") + ": " + c.name,
      message: t("deleteConfirm", { name: c.name }) + (c.role === "main" ? " (" + t("roleMain") + ")" : ""),
    });
    if (ok) await run(() => getRepository().deleteCharacter(activeProjectId, c.id));
  };

  return (
    <div className="space-y-3">
      {!compact && (
        <div>
          <h1 className="text-[22px] font-semibold leading-tight tracking-tight text-foreground">{t("title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>
        </div>
      )}

      {notice && (
        <p role="alert" className="rounded-md border border-border bg-muted/40 px-3 py-2 text-[13px] text-semantic-danger">
          {notice}
        </p>
      )}
      <AnimatePresence initial={false}>
        {aiOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="space-y-2 rounded-2xl border border-border bg-gradient-to-br from-brand/5 to-transparent p-3">
              <div className="flex items-center gap-2 text-[13px] font-medium">
                <Wand2 className="h-4 w-4 text-brand" />
                <span>Mô tả nhân vật, AI sẽ dựng hồ sơ</span>
                <button type="button" title="Đóng" aria-label="Đóng" onClick={() => setAiOpen(false)} className="ml-auto flex h-6 w-6 items-center justify-center rounded-full hover:bg-accent"><X className="h-3.5 w-3.5" /></button>
              </div>
              <textarea
                autoFocus
                rows={3}
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) generateWithAi(); }}
                placeholder="Ví dụ: Bác sĩ cú mèo tên Cú Mèo, 140cm, hiền và thông minh, đeo kính gọng vàng"
                className="w-full rounded-xl border border-border bg-card px-3 py-2 text-sm"
              />
              {aiBusy ? (
                <AiLoading label="AI đang dựng hồ sơ nhân vật…" lines={3} />
              ) : (
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">{isMockMode ? "Chế độ chạy thử: bản nháp theo quy tắc ($0)" : "Gemini (có phí)"} · Ctrl+Enter</span>
                  <Button size="icon" onClick={generateWithAi} disabled={!aiPrompt.trim()} title="Tạo" aria-label="Tạo">
                    <Wand2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {characters.length === 0 && !aiOpen && (
        <EmptyActions
          items={[
            { key: "manual", icons: [Pencil], title: "Tạo thủ công", hint: "Điền hồ sơ: tên, chiều cao, giọng, khóa nhận diện", onClick: () => openForm() },
            { key: "ai", icons: [Wand2], title: "Tạo bằng AI", hint: "Mô tả bằng lời, AI dựng hồ sơ để bạn duyệt", onClick: () => setAiOpen(true) },
            { key: "voice", icons: [Sparkles], title: "Từ Clone Giọng", hint: "Tải mẫu âm thanh/video, OmniVoice clone giọng rồi tạo nhân vật", onClick: () => setVoiceCloneOpen(true) },
          ]}
        />
      )}

      {characters.length > 0 && (
        <div className={cn("grid grid-cols-1 gap-3", !compact && "gap-4 lg:grid-cols-[280px_1fr]")}>
          <aside className="space-y-3">
            <CharacterStrip
              characters={characters}
              selectedId={selectedId}
              onSelect={(id) => {
                usePreview.getState().close();
                setSelectedId(id);
              }}
              title={t("title")}
              addOpen={createMenu}
              onToggleAdd={() => setCreateMenu(true)}
              onManual={() => { setCreateMenu(false); openForm(); }}
              onAi={() => { setCreateMenu(false); setAiOpen(true); }}
              onVoiceClone={() => { setCreateMenu(false); setVoiceCloneOpen(true); }}
              roleLabel={(c) => `${c.role === "main" ? t("roleMain") : t("roleSupporting")} · ${t("cm", { value: c.heightCm })}`}
            />
            {!compact && <ScaleLockGraph characters={characters} />}
          </aside>

          <div className="min-w-0">
            {selected ? (
              <CharacterDetail
                key={selected.id}
                character={selected}
                busy={busy}
                onEdit={() => openForm(selected)}
                onDuplicate={() => handleDuplicate(selected)}
                onDelete={() => handleDelete(selected)}
                onAddToScript={() => {
                  // Nhân vật thuộc dự án khác dự án đang mở thì chuyển sang dự án đó trước
                  if (activeProjectId !== storeProjectId) useStudioStore.getState().switchProject(activeProjectId);
                  addCharacterNodeToStore(selected);
                  queueCharacterForStudio(selected);
                  router.push("/studio");
                }}
                onSetPrimary={(name) => run(() => patch(selected, { primaryImage: name }))}
                onRemoveImage={async (name) => {
                  const ok = await confirm({ tone: "danger", title: t("removeImage"), message: t("removeImageConfirm", { name }) });
                  if (ok) await run(() => deleteCharacterImage(activeProjectId, selected.id, name));
                }}
                onUploadImages={(files) =>
                  run(async () => {
                    for (const f of files) await uploadCharacterImage(activeProjectId, selected.id, f);
                  }, true)
                }
                onUploadVoice={(f) => run(() => uploadVoiceSample(selected.voiceId, f), true)}
                onCloneVoice={async (fileOrName) => {
                  const ok = await confirm({
                    tone: "info",
                    title: "Xác nhận nhân bản giọng (OmniVoice)",
                    message: "Bạn xác nhận đây là giọng của chính bạn hoặc người đã đồng ý rõ ràng để tạo hồ sơ âm thanh cho nhân vật?",
                    confirmLabel: "Nhân bản giọng",
                  });
                  if (!ok) return;
                  await run(async () => {
                    const res = await cloneCharacterVoice(activeProjectId, {
                      voiceId: selected.voiceId || selected.id,
                      characterId: selected.id,
                      sourceFile: typeof fileOrName === "string" ? fileOrName : undefined,
                      file: typeof fileOrName === "object" ? fileOrName : undefined,
                      consentConfirmed: true,
                    });
                    await patch(selected, {
                      voiceId: res.voiceId,
                      sampleAudioUrl: res.sampleUrl || `/voices/${res.voiceId}/sample`,
                    });
                  }, true);
                }}
                onUseSample={(rel) => run(() => patch(selected, { sampleAudioUrl: rel }))}
                onAddMemory={(field, value) =>
                  run(() =>
                    patch(selected, {
                      memory: {
                        ...selected.memory,
                        [field]: field === "personality" ? value : [...(selected.memory[field] ?? []), value],
                      },
                    })
                  )
                }
              />
            ) : (
              <p className="text-sm text-muted-foreground">{t("selectHint")}</p>
            )}
          </div>
        </div>
      )}

      {/* Modal Clone Voice hỗ trợ tạo nhân vật mới trực tiếp từ giọng nói */}
      <VoiceCloneModal
        isOpen={voiceCloneOpen}
        onClose={() => setVoiceCloneOpen(false)}
        projectId={activeProjectId}
        onSuccess={(res) => {
          setVoiceCloneOpen(false);
          openForm(undefined, {
            name: res.name || res.voiceId,
            voiceId: res.voiceId,
          });
        }}
      />
    </div>
  );
}
