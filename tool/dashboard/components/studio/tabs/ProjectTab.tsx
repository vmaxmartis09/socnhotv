"use client";

import React, { useMemo, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import type { CharacterProfileSection } from "@/store/slices/rightPanelSlice";
import { getRepository } from "@/lib/repositories";
import type { Character, CharacterImageAsset } from "@/lib/repositories/types";
import { CORE_URL } from "@/lib/repositories/core";
import { cloneCharacterVoice } from "@/lib/repositories/character-assets";
import { VoiceCloneModal } from "@/components/voice/VoiceCloneModal";
import {
  Plus,
  Search,
  Copy,
  Trash2,
  Upload,
  Play,
  Volume2,
  X,
  Check,
  Maximize2,
  Loader2,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export function ProjectTab() {
  const t = useTranslations("projectTab");
  const c = useTranslations("common");
  const {
    activeProjectId,
    projects,
    episodes,
    activeEpisodeId,
    selectEpisode,
    characters,
    upsertCharacterInStore,
    removeCharacterFromStore,
    selectedCharacterId,
    setSelectedCharacterId,
    activeCharacterSection,
    setActiveCharacterSection,
    nodes,
    edges,
    setNodesAndEdges,
    setSelectedNodeId,
    flashNode,
  } = useStudioStore();

  const [charSearch, setCharSearch] = useState("");
  const [confirmDeleteCharId, setConfirmDeleteCharId] = useState<string | null>(
    null
  );
  const [lightboxImage, setLightboxImage] =
    useState<CharacterImageAsset | null>(null);
  const [savedToast, setSavedToast] = useState(false);

  // Voice tab states
  const [ttsSentence, setTtsSentence] = useState(t("voice.testInputDefault"));
  const [ttsTempo, setTtsTempo] = useState(1.1);
  const [ttsPreviewUrl, setTtsPreviewUrl] = useState<string | null>(null);
  const [ttsSpeaking, setTtsSpeaking] = useState(false);
  const [cloneModalOpen, setCloneModalOpen] = useState(false);
  const [cloneConsentChecked, setCloneConsentChecked] = useState(false);
  const [cloneNewVoiceId, setCloneNewVoiceId] = useState("soc-nho-custom");
  const [cloneFile, setCloneFile] = useState<File | null>(null);
  const [cloneDialect, setCloneDialect] = useState<"south" | "north" | "central">("south");
  const [cloneBusy, setCloneBusy] = useState(false);
  const [cloneError, setCloneError] = useState("");

  const photoInputRef = useRef<HTMLInputElement>(null);
  const sampleAudioRef = useRef<HTMLAudioElement>(null);

  const project = projects.find((p) => p.id === activeProjectId);
  const selectedChar = characters.find((ch) => ch.id === selectedCharacterId);

  const filteredCharacters = useMemo(() => {
    const q = charSearch.trim().toLowerCase();
    if (!q) return characters;
    return characters.filter(
      (ch) =>
        ch.name.toLowerCase().includes(q) ||
        ch.id.toLowerCase().includes(q) ||
        ch.voiceId.toLowerCase().includes(q) ||
        ch.role.toLowerCase().includes(q)
    );
  }, [characters, charSearch]);

  const handleSaveCharacter = async (updated: Character) => {
    upsertCharacterInStore(updated);
    setSavedToast(true);
    window.setTimeout(() => setSavedToast(false), 1800);
    try {
      await getRepository().upsertCharacter(activeProjectId, updated);
    } catch {
      // already in store
    }
  };

  const handleAddCharacter = async () => {
    const newId = `char_${Date.now().toString(36)}`;
    const newChar: Character = {
      id: newId,
      projectId: activeProjectId,
      name: "Nhân vật phụ mới",
      role: "supporting",
      description: "Nhân vật phụ trong thế giới khu rừng Sóc Nhỏ TV.",
      heightCm: 120,
      scaleRatio: 1.2,
      voiceId: "soc-nho",
      defaultTempo: 1.0,
      sampleAudioUrl: "/demo/audio/soc-nho_sample.mp3",
      promptLock:
        "3D Pixar-style cute woodland character, 120cm height, warm colors",
      referenceImages: ["/demo/characters/soc_nho_04.png"],
      referenceLibrary: [
        {
          id: "img_init_1",
          url: "/demo/characters/soc_nho_04.png",
          angle: "Chính diện",
          isPrimary: true,
          source: "upload",
          createdAt: new Date().toISOString(),
        },
      ],
      generatedClips: [],
      appearances: [],
      memory: {
        personality: "Thân thiện, vui vẻ",
        catchphrases: ["Chào bạn nha!"],
        habits: ["Hay cười"],
        pastEvents: [],
        pastEventsSummary: [],
      },
    };
    await handleSaveCharacter(newChar);
    setSelectedCharacterId(newChar.id);
    setActiveCharacterSection("profile");
  };

  const handleDuplicateCharacter = async (ch: Character) => {
    const copy: Character = {
      ...ch,
      id: `${ch.id}_copy_${Date.now().toString(36).slice(-3)}`,
      name: `${ch.name} (Bản sao)`,
      role: "supporting",
    };
    await handleSaveCharacter(copy);
  };

  const handleConfirmDeleteCharacter = async (id: string) => {
    removeCharacterFromStore(id);
    if (selectedCharacterId === id) {
      setSelectedCharacterId(null);
    }
    setConfirmDeleteCharId(null);
    try {
      await getRepository().deleteCharacter(activeProjectId, id);
    } catch {
      // ignore
    }
  };

  const handleDropCharacterToCanvas = (ch: Character) => {
    const newNodeId = `node_char_${ch.id}_${Date.now().toString(36).slice(-3)}`;
    const newNode = {
      id: newNodeId,
      type: "studioCard",
      position: { x: 370, y: 420 + (nodes.length % 3) * 40 },
      selected: true,
      data: {
        nodeType: "character",
        status: "idle" as const,
        params: { characterId: ch.id },
        generations: [],
        nextStepHint: `Hồ sơ DNA ${ch.name} (${ch.heightCm} cm)`,
      },
    };
    setNodesAndEdges(
      [...nodes.map((n) => ({ ...n, selected: false })), newNode],
      edges,
      true
    );
    setSelectedNodeId(newNodeId);
    flashNode(newNodeId);
  };

  const handleUploadReferencePhoto = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!selectedChar) return;
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result !== "string") return;
      const newAsset: CharacterImageAsset = {
        id: `ref_${Date.now().toString(36)}`,
        url: reader.result,
        angle: "Tải lên mới",
        isPrimary: false,
        source: "upload",
        createdAt: new Date().toISOString(),
      };
      const lib = [...(selectedChar.referenceLibrary || []), newAsset];
      handleSaveCharacter({
        ...selectedChar,
        referenceImages: [
          selectedChar.referenceImages[0] || reader.result,
          ...lib.map((x) => x.url).slice(1),
        ],
        referenceLibrary: lib,
      });
    };
    reader.readAsDataURL(file);
  };

  const handleGeneratePhotoByNode = (ch: Character) => {
    const newNodeId = `node_img_${ch.id}_${Date.now().toString(36).slice(-3)}`;
    const newNode = {
      id: newNodeId,
      type: "studioCard",
      position: { x: 700, y: 240 },
      selected: true,
      data: {
        nodeType: "image_gen",
        status: "succeeded" as const,
        params: {
          model: "gemini-2.5-flash-image",
          aspectRatio: "9:16",
          prompt: `${ch.promptLock}, multi-angle reference turnaround sheet`,
        },
        previewType: "image" as const,
        previewUrl: ch.referenceImages[0] || "/demo/characters/soc_nho_03.png",
        summaryText: `Ảnh tham chiếu mới cho ${ch.name}`,
        generations: [],
      },
    };
    setNodesAndEdges(
      [...nodes.map((n) => ({ ...n, selected: false })), newNode],
      edges,
      true
    );
    setSelectedNodeId(newNodeId);
    flashNode(newNodeId);
  };

  const handleSetPrimaryPhoto = (assetId: string) => {
    if (!selectedChar) return;
    const lib = (selectedChar.referenceLibrary || []).map((item) => ({
      ...item,
      isPrimary: item.id === assetId,
    }));
    const primary = lib.find((x) => x.isPrimary) || lib[0];
    const orderedUrls = primary
      ? [
          primary.url,
          ...lib.filter((x) => x.id !== primary.id).map((x) => x.url),
        ]
      : selectedChar.referenceImages;
    handleSaveCharacter({
      ...selectedChar,
      referenceImages: orderedUrls,
      referenceLibrary: lib,
    });
  };

  const handleDeletePhoto = (assetId: string) => {
    if (!selectedChar) return;
    const lib = (selectedChar.referenceLibrary || []).filter(
      (item) => item.id !== assetId
    );
    handleSaveCharacter({
      ...selectedChar,
      referenceImages: lib.map((x) => x.url),
      referenceLibrary: lib,
    });
  };

  const handleTestOmniVoice = async () => {
    if (!selectedChar) return;
    setTtsSpeaking(true);
    try {
      const res = await fetch(
        `${CORE_URL}/projects/${activeProjectId}/voice/preview`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: ttsSentence,
            voiceId: selectedChar.voiceId,
            tempo: ttsTempo,
          }),
        }
      );
      if (res.ok) {
        const data = await res.json();
        setTtsPreviewUrl(data.audioUrl || "/demo/audio/canh_01.mp3");
      } else {
        setTtsPreviewUrl("/demo/audio/canh_01.mp3");
      }
    } catch {
      setTtsPreviewUrl("/demo/audio/canh_01.mp3");
    } finally {
      setTtsSpeaking(false);
    }
  };

  const handleConfirmVoiceClone = async () => {
    if (!selectedChar || !cloneConsentChecked || !cloneNewVoiceId.trim())
      return;
    const newVid = cloneNewVoiceId.trim();
    setCloneBusy(true);
    setCloneError("");
    try {
      const res = await cloneCharacterVoice(activeProjectId, {
        voiceId: newVid,
        characterId: selectedChar.id,
        file: cloneFile || undefined,
        dialect: cloneDialect,
        consentConfirmed: true,
      });
      await handleSaveCharacter({
        ...selectedChar,
        voiceId: newVid,
        sampleAudioUrl: res?.sampleUrl || `/voices/${newVid}/sample`,
      });
      setCloneModalOpen(false);
      setCloneConsentChecked(false);
      setCloneFile(null);
    } catch (err: any) {
      setCloneError(err.message || "Không thể nhân bản giọng nói. Hãy kiểm tra tệp âm thanh nguồn.");
    } finally {
      setCloneBusy(false);
    }
  };

  // If a character is selected, render its FULL 5-section profile!
  if (selectedChar) {
    const refLib: CharacterImageAsset[] =
      selectedChar.referenceLibrary && selectedChar.referenceLibrary.length > 0
        ? selectedChar.referenceLibrary
        : selectedChar.referenceImages.map((url, idx) => ({
            id: `img_${idx}`,
            url,
            angle: idx === 0 ? "Chính diện" : `Góc ${idx + 1}`,
            isPrimary: idx === 0,
            source: "upload" as const,
            createdAt: "2026-11-01T10:00:00Z",
          }));

    const clips = selectedChar.generatedClips || [];
    const referencingNodes = nodes.filter(
      (n) =>
        (n.data.nodeType === "character" &&
          n.data.params?.characterId === selectedChar.id) ||
        (n.data.nodeType === "voice_tts" &&
          n.data.params?.voiceId === selectedChar.voiceId)
    );

    const sections: Array<{ id: CharacterProfileSection; label: string }> = [
      { id: "profile", label: t("sections.profile") },
      { id: "images", label: t("sections.images", { count: refLib.length }) },
      { id: "videos", label: t("sections.videos", { count: clips.length }) },
      { id: "voice", label: t("sections.voice") },
      { id: "usage", label: t("sections.usage") },
    ];

    return (
      <div className="p-3.5 space-y-3.5 text-xs">
        {/* Top bar: Back to character list + Drop onto canvas */}
        <div className="flex items-center justify-between gap-2 border-b border-border pb-2.5">
          <button
            type="button"
            onClick={() => setSelectedCharacterId(null)}
            className="rounded border border-border bg-card px-2 py-1 text-xs font-medium text-foreground hover:bg-accent"
          >
            ← {t("backToList")}
          </button>
          <button
            type="button"
            onClick={() => handleDropCharacterToCanvas(selectedChar)}
            className="rounded bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground"
          >
            + {t("dropToCanvasBtn")}
          </button>
        </div>

        {/* Character summary header */}
        <div className="flex items-center gap-3">
          {selectedChar.referenceImages[0] && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={selectedChar.referenceImages[0]}
              alt={selectedChar.name}
              className="h-12 w-12 shrink-0 rounded-md border border-border object-cover object-top"
            />
          )}
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-foreground">
              {selectedChar.name}
            </h3>
            <p className="text-[13px] text-muted-foreground tnum">
              {selectedChar.role === "main"
                ? t("profile.roleMain")
                : t("profile.roleSupporting")}{" "}
              · {selectedChar.heightCm} cm ({selectedChar.scaleRatio}x) ·{" "}
              <code>{selectedChar.voiceId}</code>
            </p>
          </div>
          {savedToast && (
            <span className="rounded bg-semantic-success/15 px-2 py-0.5 text-[13px] font-medium text-semantic-success">
              {t("profile.savedToast")}
            </span>
          )}
        </div>

        {/* 5 Section Tabs */}
        <div
          role="tablist"
          className="flex flex-wrap gap-1 border-b border-border pb-2"
        >
          {sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              role="tab"
              aria-selected={activeCharacterSection === sec.id}
              onClick={() => setActiveCharacterSection(sec.id)}
              className={cn(
                "h-7 rounded-md px-2 text-xs font-medium transition-colors",
                activeCharacterSection === sec.id
                  ? "bg-accent text-foreground border border-border"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {sec.label}
            </button>
          ))}
        </div>

        {/* Section A: Hồ sơ (Profile + Memory + ScaleLock Comparison) */}
        {activeCharacterSection === "profile" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <label className="space-y-1">
                <span className="text-muted-foreground">
                  {t("profile.name")}
                </span>
                <input
                  type="text"
                  value={selectedChar.name}
                  onChange={(e) =>
                    handleSaveCharacter({
                      ...selectedChar,
                      name: e.target.value,
                    })
                  }
                  className="h-7 w-full rounded border border-border bg-card px-2 text-xs text-foreground"
                />
              </label>
              <label className="space-y-1">
                <span className="text-muted-foreground">
                  {t("profile.role")}
                </span>
                <select
                  value={selectedChar.role}
                  onChange={(e) =>
                    handleSaveCharacter({
                      ...selectedChar,
                      role: e.target.value as "main" | "supporting",
                    })
                  }
                  className="h-7 w-full rounded border border-border bg-card px-2 text-xs text-foreground"
                >
                  <option value="main">{t("profile.roleMain")}</option>
                  <option value="supporting">
                    {t("profile.roleSupporting")}
                  </option>
                </select>
              </label>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <label className="space-y-1">
                <span className="text-muted-foreground">
                  {t("profile.heightCm")}
                </span>
                <input
                  type="number"
                  value={selectedChar.heightCm}
                  onChange={(e) => {
                    const cm = Number(e.target.value) || 100;
                    handleSaveCharacter({
                      ...selectedChar,
                      heightCm: cm,
                      scaleRatio: Number((cm / 100).toFixed(2)),
                    });
                  }}
                  className="h-7 w-full rounded border border-border bg-card px-2 text-xs tnum text-foreground"
                />
              </label>
              <label className="space-y-1">
                <span className="text-muted-foreground">
                  {t("profile.scaleRatio")}
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={selectedChar.scaleRatio}
                  readOnly
                  className="h-7 w-full rounded border border-border bg-muted px-2 text-xs tnum text-muted-foreground"
                />
              </label>
            </div>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.description")}
              </span>
              <textarea
                rows={2}
                value={selectedChar.description || ""}
                onChange={(e) =>
                  handleSaveCharacter({
                    ...selectedChar,
                    description: e.target.value,
                  })
                }
                className="w-full rounded border border-border bg-card p-2 text-xs text-foreground"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.promptLock")}
              </span>
              <textarea
                rows={2}
                value={selectedChar.promptLock}
                onChange={(e) =>
                  handleSaveCharacter({
                    ...selectedChar,
                    promptLock: e.target.value,
                  })
                }
                className="w-full rounded border border-border bg-card p-2 font-mono text-[13px] text-foreground"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.personality")}
              </span>
              <input
                type="text"
                value={selectedChar.memory.personality}
                onChange={(e) =>
                  handleSaveCharacter({
                    ...selectedChar,
                    memory: {
                      ...selectedChar.memory,
                      personality: e.target.value,
                    },
                  })
                }
                className="h-7 w-full rounded border border-border bg-card px-2 text-xs text-foreground"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.catchphrases")}
              </span>
              <textarea
                rows={2}
                value={selectedChar.memory.catchphrases.join("\n")}
                onChange={(e) =>
                  handleSaveCharacter({
                    ...selectedChar,
                    memory: {
                      ...selectedChar.memory,
                      catchphrases: e.target.value
                        .split("\n")
                        .filter((x) => x.trim()),
                    },
                  })
                }
                className="w-full rounded border border-border bg-card p-2 text-xs text-foreground"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.habits")}
              </span>
              <textarea
                rows={2}
                value={selectedChar.memory.habits.join("\n")}
                onChange={(e) =>
                  handleSaveCharacter({
                    ...selectedChar,
                    memory: {
                      ...selectedChar.memory,
                      habits: e.target.value
                        .split("\n")
                        .filter((x) => x.trim()),
                    },
                  })
                }
                className="w-full rounded border border-border bg-card p-2 text-xs text-foreground"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-muted-foreground">
                {t("profile.pastEvents")}
              </span>
              <textarea
                rows={3}
                value={(
                  selectedChar.memory.pastEvents ||
                  selectedChar.memory.pastEventsSummary ||
                  []
                ).join("\n")}
                onChange={(e) => {
                  const evs = e.target.value
                    .split("\n")
                    .filter((x) => x.trim());
                  handleSaveCharacter({
                    ...selectedChar,
                    memory: {
                      ...selectedChar.memory,
                      pastEvents: evs,
                      pastEventsSummary: evs,
                    },
                  });
                }}
                className="w-full rounded border border-border bg-card p-2 text-xs text-foreground"
              />
            </label>
          </div>
        )}

        {/* Section B: Ảnh (Multi-angle Reference Image Library + Lightbox + Provenance) */}
        {activeCharacterSection === "images" && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                ref={photoInputRef}
                type="file"
                accept="image/*"
                onChange={handleUploadReferencePhoto}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => photoInputRef.current?.click()}
                className="flex h-7 items-center gap-1 rounded border border-border bg-card px-2.5 text-xs font-medium text-foreground hover:bg-accent"
              >
                <Upload className="h-3.5 w-3.5" />
                <span>{t("images.uploadBtn")}</span>
              </button>
              <button
                type="button"
                onClick={() => handleGeneratePhotoByNode(selectedChar)}
                className="flex h-7 items-center gap-1 rounded border border-border bg-card px-2.5 text-xs font-medium text-foreground hover:bg-accent"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>{t("images.generateByNodeBtn")}</span>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {refLib.map((asset) => (
                <div
                  key={asset.id}
                  className={cn(
                    "rounded-md border bg-card p-2 space-y-1.5",
                    asset.isPrimary ? "border-brand" : "border-border"
                  )}
                >
                  <div className="relative overflow-hidden rounded border border-border bg-muted/20">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={asset.url}
                      alt={asset.angle}
                      className="h-28 w-full object-cover object-top"
                    />
                    {asset.isPrimary && (
                      <span className="absolute left-1.5 top-1.5 rounded bg-brand px-1.5 py-0.5 text-xs font-medium text-white">
                        {t("images.primaryBadge")}
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => setLightboxImage(asset)}
                      title={t("images.viewLargeBtn")}
                      aria-label={t("images.viewLargeBtn")}
                      className="absolute right-1.5 top-1.5 flex h-6 w-6 items-center justify-center rounded border border-border bg-card/90 text-foreground"
                    >
                      <Maximize2 className="h-3 w-3" />
                    </button>
                  </div>

                  <p className="truncate font-medium text-foreground">
                    {t("images.angleLabel", { angle: asset.angle })}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {asset.source === "upload"
                      ? t("images.sourceUpload")
                      : t("images.sourceGenerated", {
                          model: asset.model || "gemini-2.5-flash-image",
                        })}
                  </p>
                  {asset.prompt && (
                    <p className="truncate font-mono text-xs text-muted-foreground">
                      {asset.prompt}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-1">
                    {!asset.isPrimary ? (
                      <button
                        type="button"
                        onClick={() => handleSetPrimaryPhoto(asset.id)}
                        className="rounded border border-border px-1.5 py-0.5 text-xs text-foreground hover:bg-accent"
                      >
                        {t("images.setPrimaryBtn")}
                      </button>
                    ) : (
                      <span />
                    )}
                    <button
                      type="button"
                      onClick={() => handleDeletePhoto(asset.id)}
                      aria-label={c("delete")}
                      className="rounded p-1 text-muted-foreground hover:text-semantic-danger"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {lightboxImage && (
              <div
                role="dialog"
                aria-modal="true"
                className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4"
              >
                <div className="max-w-lg w-full rounded-lg border border-border bg-popover p-4 text-popover-foreground space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{lightboxImage.angle}</span>
                    <button
                      type="button"
                      onClick={() => setLightboxImage(null)}
                      aria-label={c("close")}
                      className="rounded p-1 hover:bg-accent"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={lightboxImage.url}
                    alt={lightboxImage.angle}
                    className="max-h-[65dvh] w-full rounded border border-border object-contain bg-background"
                  />
                  <p className="text-[13px] text-muted-foreground">
                    {lightboxImage.source === "upload"
                      ? t("images.sourceUpload")
                      : `${lightboxImage.model || "AI"} — ${
                          lightboxImage.prompt || ""
                        }`}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Section C: Video (Generated clips featuring this character) */}
        {activeCharacterSection === "videos" && (
          <div className="space-y-2.5">
            {clips.length === 0 ? (
              <p className="text-muted-foreground">{t("videos.empty")}</p>
            ) : (
              clips.map((clip) => (
                <div
                  key={clip.id}
                  className="rounded-md border border-border bg-card p-2.5 space-y-2"
                >
                  <video
                    src={clip.url}
                    controls
                    preload="metadata"
                    className="h-40 w-full rounded border border-border object-cover bg-muted/20"
                  />
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">
                      {t("videos.episodeScene", {
                        episode: clip.episodeTitle,
                        scene: clip.sceneLabel,
                      })}
                    </span>
                    <span className="font-mono text-[13px] text-muted-foreground tnum">
                      {clip.durationSec}s
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Section D: Giọng (Voice-ID soc-nho, Sample, OmniVoice test reader, Tempo, Consent Clone Modal) */}
        {activeCharacterSection === "voice" && (
          <div className="space-y-3">
            <div className="rounded-md border border-border bg-card p-2.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">
                  {t("voice.voiceIdLabel")}
                </span>
                <code className="rounded bg-accent px-2 py-0.5 font-mono text-xs font-semibold text-foreground">
                  {selectedChar.voiceId}
                </code>
              </div>

              <audio
                ref={sampleAudioRef}
                src={
                  selectedChar.sampleAudioUrl ||
                  "/demo/audio/soc-nho_sample.mp3"
                }
                controls
                preload="metadata"
                className="h-8 w-full"
              />
            </div>

            <div className="rounded-md border border-border bg-card p-2.5 space-y-2.5">
              <label className="block space-y-1">
                <span className="font-medium text-foreground">
                  {t("voice.tempoLabel", { tempo: ttsTempo.toFixed(2) })}
                </span>
                <input
                  type="range"
                  min="0.8"
                  max="1.4"
                  step="0.05"
                  value={ttsTempo}
                  onChange={(e) => setTtsTempo(Number(e.target.value))}
                  className="w-full accent-brand"
                />
              </label>

              <label className="block space-y-1">
                <span className="font-medium text-foreground">
                  {t("voice.testInputLabel")}
                </span>
                <textarea
                  rows={3}
                  value={ttsSentence}
                  onChange={(e) => setTtsSentence(e.target.value)}
                  className="w-full rounded border border-border bg-background p-2 text-xs text-foreground"
                />
              </label>

              <button
                type="button"
                onClick={handleTestOmniVoice}
                disabled={ttsSpeaking}
                className="flex h-8 w-full items-center justify-center gap-1.5 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground"
              >
                <Volume2 className="h-3.5 w-3.5" />
                <span>
                  {ttsSpeaking ? t("voice.speaking") : t("voice.testSpeakBtn")}
                </span>
              </button>

              {ttsPreviewUrl && (
                <div className="pt-1">
                  <audio
                    src={ttsPreviewUrl}
                    controls
                    autoPlay
                    className="h-8 w-full"
                  />
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => setCloneModalOpen(true)}
              className="h-8 w-full rounded-md border border-border bg-card px-3 text-xs font-medium text-foreground hover:bg-accent"
            >
              {t("voice.cloneVoiceBtn")}
            </button>

            {/* Voice Clone Modal */}
            <VoiceCloneModal
              isOpen={cloneModalOpen}
              onClose={() => setCloneModalOpen(false)}
              defaultVoiceId={selectedChar.voiceId || selectedChar.id}
              projectId={activeProjectId}
              characterId={selectedChar.id}
              sourceSamples={(selectedChar.voiceFiles ?? []).map((f) => ({ name: f.name, url: f.url }))}
              onSuccess={async (res) => {
                await handleSaveCharacter({
                  ...selectedChar,
                  voiceId: res.voiceId,
                  sampleAudioUrl: res.sampleUrl || `/voices/${res.voiceId}/sample`,
                });
                setCloneModalOpen(false);
              }}
            />
          </div>
        )}

        {/* Section E: Dùng ở đâu (Episodes/Scenes & Referencing Canvas Nodes) */}
        {activeCharacterSection === "usage" && (
          <div className="space-y-3.5">
            <div className="space-y-2 border-b border-border pb-3">
              <h4 className="font-semibold text-foreground">
                {t("usage.episodesTitle")}
              </h4>
              <ul className="space-y-1.5">
                {(selectedChar.appearances || []).map((ap, i) => (
                  <li
                    key={i}
                    className="rounded border border-border bg-card p-2 space-y-0.5"
                  >
                    <p className="font-medium text-foreground">
                      {ap.episodeTitle}
                    </p>
                    <p className="text-[13px] text-muted-foreground">
                      {ap.scenes.join(" · ")}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="font-semibold text-foreground">
                {t("usage.canvasNodesTitle")}
              </h4>
              {referencingNodes.length === 0 ? (
                <p className="text-muted-foreground">{t("usage.noNodes")}</p>
              ) : (
                <ul className="space-y-1.5">
                  {referencingNodes.map((n) => (
                    <li
                      key={n.id}
                      className="flex items-center justify-between rounded border border-border bg-card p-2"
                    >
                      <div>
                        <p className="font-mono font-medium text-foreground">
                          {n.id}
                        </p>
                        <p className="text-[13px] text-muted-foreground">
                          {n.data.nodeType}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedNodeId(n.id);
                          flashNode(n.id);
                        }}
                        className="rounded border border-border bg-card px-2 py-1 text-[13px] font-medium text-foreground hover:bg-accent"
                      >
                        {t("usage.jumpToNodeBtn")}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Default view of ProjectTab: Project overview + Episodes + Character Cards List
  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Project summary */}
      <section className="rounded-md border border-border bg-card p-3 space-y-1.5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            {project?.name || "Sóc Nhỏ TV"}
          </h3>
          <span className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[13px] tnum">
            {project?.defaultAspectRatio || "9:16"} ·{" "}
            {project?.defaultVoiceId || "soc-nho"}
          </span>
        </div>
        <p className="text-[13px] text-muted-foreground leading-snug">
          {project?.description}
        </p>
      </section>

      {/* Episodes list */}
      <section className="space-y-2 border-b border-border pb-3.5">
        <h3 className="font-semibold text-foreground tnum">
          {t("episodesTitle", { count: episodes.length })}
        </h3>
        <ul className="space-y-1">
          {episodes.map((ep) => (
            <li key={ep.id}>
              <button
                type="button"
                onClick={() => selectEpisode(ep.id)}
                className={cn(
                  "flex w-full items-center justify-between rounded border px-2.5 py-1.5 text-left",
                  ep.id === activeEpisodeId
                    ? "border-foreground bg-accent font-medium text-foreground"
                    : "border-border bg-card text-muted-foreground hover:text-foreground"
                )}
              >
                <span className="truncate">{ep.title}</span>
                <span className="shrink-0 font-mono text-[13px] tnum">
                  {ep.nodeCount} bước
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {/* Characters inside Project (Change 1) */}
      <section className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground tnum">
            {t("charactersTitle", { count: characters.length })}
          </h3>
          <button
            type="button"
            onClick={handleAddCharacter}
            className="flex h-6 items-center gap-1 rounded border border-border bg-card px-2 text-[13px] font-medium text-foreground hover:bg-accent"
          >
            <Plus className="h-3 w-3" />
            <span>{t("addCharacterBtn")}</span>
          </button>
        </div>

        <p className="text-[13px] text-muted-foreground leading-snug">
          {t("dragHint")}
        </p>

        {/* Character search */}
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="search"
            value={charSearch}
            onChange={(e) => setCharSearch(e.target.value)}
            placeholder={t("searchCharacters")}
            className="h-7 w-full rounded-md border border-border bg-card pl-7 pr-2 text-xs text-foreground"
          />
        </div>

        {/* Character cards */}
        <ul className="space-y-2">
          {filteredCharacters.map((ch) => (
            <li
              key={ch.id}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData("application/x-studio-character", ch.id);
              }}
              className="rounded-md border border-border bg-card p-2.5 space-y-2 cursor-grab active:cursor-grabbing hover:border-foreground/50"
            >
              <div
                onClick={() => {
                  setSelectedCharacterId(ch.id);
                  setActiveCharacterSection("profile");
                }}
                className="flex items-center gap-2.5 cursor-pointer"
              >
                {ch.referenceImages[0] ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={ch.referenceImages[0]}
                    alt={ch.name}
                    className="h-11 w-11 shrink-0 rounded border border-border object-cover object-top"
                  />
                ) : (
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded border border-border bg-accent font-semibold">
                    {ch.name.charAt(0)}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-1">
                    <p className="truncate font-semibold text-foreground">
                      {ch.name}
                    </p>
                    <span className="shrink-0 font-mono text-[13px] tnum text-muted-foreground">
                      {ch.heightCm} cm ({ch.scaleRatio}x)
                    </span>
                  </div>
                  <p className="truncate text-[13px] text-muted-foreground">
                    {ch.role === "main"
                      ? t("profile.roleMain")
                      : t("profile.roleSupporting")}{" "}
                    · <code>{ch.voiceId}</code>
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-border/70 pt-1.5">
                <button
                  type="button"
                  onClick={() => handleDropCharacterToCanvas(ch)}
                  className="rounded border border-border bg-card px-2 py-0.5 text-[13px] font-medium text-foreground hover:bg-accent"
                >
                  + {t("dropToCanvasBtn")}
                </button>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleDuplicateCharacter(ch)}
                    title={t("duplicateBtn")}
                    aria-label={t("duplicateBtn")}
                    className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDeleteCharId(ch.id)}
                    title={t("deleteBtn")}
                    aria-label={t("deleteBtn")}
                    className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-semantic-danger"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {confirmDeleteCharId === ch.id && (
                <div className="rounded border border-semantic-danger/40 bg-accent/50 p-2 space-y-1.5">
                  <p className="text-[13px] text-semantic-danger">
                    {t("deleteConfirmText", { name: ch.name })}
                  </p>
                  <div className="flex justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => setConfirmDeleteCharId(null)}
                      className="h-6 rounded border border-border bg-card px-2 text-[13px]"
                    >
                      {c("cancel")}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleConfirmDeleteCharacter(ch.id)}
                      className="h-6 rounded bg-semantic-danger px-2 text-[13px] font-medium text-white"
                    >
                      {c("delete")}
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>

      </section>
    </div>
  );
}
