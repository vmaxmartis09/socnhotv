"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Mic,
  Play,
  Pause,
  Sparkles,
  AudioLines,
  Plus,
} from "@/components/ui/icons";
import {
  fetchVoiceVault,
  type VoiceVaultItem,
  type VoiceCloneResult,
} from "@/lib/repositories/character-assets";
import { VoiceCloneModal } from "./VoiceCloneModal";
import { CORE_URL } from "@/lib/repositories/core";
import { cn } from "@/lib/utils";

export interface VoiceSelectorWithCloneProps {
  value: string;
  onChange: (voiceId: string) => void;
  projectId?: string;
  characterId?: string;
  characterName?: string;
  sourceSamples?: Array<{ name: string; url: string }>;
  disabled?: boolean;
  className?: string;
}

export function VoiceSelectorWithClone({
  value,
  onChange,
  projectId,
  characterId,
  characterName,
  sourceSamples = [],
  disabled = false,
  className,
}: VoiceSelectorWithCloneProps) {
  const [voices, setVoices] = useState<VoiceVaultItem[]>([]);
  const [cloneModalOpen, setCloneModalOpen] = useState(false);
  const [isCustom, setIsCustom] = useState(false);
  const [customInput, setCustomInput] = useState(value);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const loadVoices = async () => {
    const list = await fetchVoiceVault();
    setVoices(list);
  };

  useEffect(() => {
    loadVoices();
  }, []);

  useEffect(() => {
    setCustomInput(value);
    const exists = voices.some((v) => v.id === value);
    if (value && !exists && voices.length > 0) {
      setIsCustom(true);
    }
  }, [value, voices]);

  // Tìm mẫu nghe thử của giọng đang chọn
  const activeVoice = voices.find((v) => v.id === value);
  const sampleUrl = activeVoice?.sampleUrl || (value ? `/voices/${value}/sample` : null);

  const togglePlaySample = () => {
    if (!sampleUrl) return;
    const fullUrl = sampleUrl.startsWith("http") ? sampleUrl : `${CORE_URL}${sampleUrl}`;

    if (!audioRef.current || audioRef.current.src !== fullUrl) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      audioRef.current = new Audio(fullUrl);
      audioRef.current.onended = () => setIsPlaying(false);
      audioRef.current.onerror = () => setIsPlaying(false);
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    }
  };

  const handleCloneSuccess = async (res: VoiceCloneResult) => {
    await loadVoices();
    onChange(res.voiceId);
    setIsCustom(false);
  };

  const defaultSuggestedVoiceId =
    characterId ||
    (characterName
      ? characterName
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/đ/g, "d")
          .replace(/[^a-z0-9_-]+/g, "-")
          .replace(/^-+|-+$/g, "")
      : "");

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center gap-1.5">
        {isCustom ? (
          <div className="flex-1 flex items-center gap-1">
            <input
              type="text"
              disabled={disabled}
              value={customInput}
              onChange={(e) => {
                setCustomInput(e.target.value);
                onChange(e.target.value);
              }}
              placeholder="nhap-ma-giong"
              className="h-8 flex-1 rounded-md border border-border bg-card px-2.5 font-mono text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
            />
            <button
              type="button"
              onClick={() => setIsCustom(false)}
              className="h-8 rounded-md border border-border px-2 text-[11px] text-muted-foreground hover:bg-accent"
            >
              Chọn từ kho
            </button>
          </div>
        ) : (
          <div className="flex-1 flex items-center gap-1">
            <select
              disabled={disabled}
              value={value}
              onChange={(e) => {
                if (e.target.value === "__custom__") {
                  setIsCustom(true);
                } else {
                  onChange(e.target.value);
                }
              }}
              className="h-8 flex-1 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value="">-- Chọn giọng trong Voice Vault --</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name || v.id} {v.dialect ? `(${v.dialect})` : ""} {v.hasSample ? "🔊" : ""}
                </option>
              ))}
              <option value="__custom__">+ Nhập mã tùy chỉnh...</option>
            </select>
          </div>
        )}

        {/* Nút nghe thử mẫu giọng nếu có */}
        {value && (
          <button
            type="button"
            title={isPlaying ? "Dừng phát" : "Nghe thử giọng"}
            onClick={togglePlaySample}
            className={cn(
              "flex h-8 items-center gap-1 rounded-md border px-2 text-xs font-medium transition-colors shrink-0",
              isPlaying
                ? "border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : "border-border bg-accent/40 text-foreground hover:bg-accent"
            )}
          >
            {isPlaying ? (
              <>
                <Pause className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Dừng</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Nghe thử</span>
              </>
            )}
          </button>
        )}

        {/* Nút mở Clone Voice Tool trực tiếp */}
        <button
          type="button"
          disabled={disabled}
          onClick={() => setCloneModalOpen(true)}
          title="Nhân bản giọng nói mới qua OmniVoice"
          className="flex h-8 items-center gap-1.5 rounded-md border border-brand/40 bg-brand/10 px-2.5 text-xs font-medium text-brand hover:bg-brand/20 transition-all shrink-0 active:scale-95 shadow-2xs"
        >
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          <span>⚡ Clone giọng</span>
        </button>
      </div>

      {/* Modal Clone Voice */}
      <VoiceCloneModal
        isOpen={cloneModalOpen}
        onClose={() => setCloneModalOpen(false)}
        defaultVoiceId={defaultSuggestedVoiceId ? `${defaultSuggestedVoiceId}` : ""}
        projectId={projectId}
        characterId={characterId}
        sourceSamples={sourceSamples}
        onSuccess={handleCloneSuccess}
      />
    </div>
  );
}
