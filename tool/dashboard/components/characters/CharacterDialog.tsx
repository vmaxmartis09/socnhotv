"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import type { Character } from "@/lib/repositories";
import { Button } from "@/components/ui/Button";

const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);

const inputCls =
  "w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1 text-[13px] font-medium text-muted-foreground">
      <span>{label}</span>
      {children}
    </label>
  );
}

interface Props {
  /** Có `initial` => sửa; không có => tạo mới. */
  initial?: Character;
  projectId: string;
  onSave: (c: Character, isNew: boolean) => Promise<void>;
  onClose: () => void;
}

export function CharacterDialog({ initial, projectId, onSave, onClose }: Props) {
  const t = useTranslations("characters");
  const isNew = !initial;
  const [id, setId] = useState(initial?.id ?? "");
  const [name, setName] = useState(initial?.name ?? "");
  const [role, setRole] = useState<Character["role"]>(initial?.role ?? "supporting");
  const [heightCm, setHeightCm] = useState(String(initial?.heightCm ?? 100));
  const [scaleRatio, setScaleRatio] = useState(String(initial?.scaleRatio ?? 1));
  const [description, setDescription] = useState(initial?.description ?? "");
  const [tempo, setTempo] = useState(String(initial?.defaultTempo ?? 1));
  const [voiceId, setVoiceId] = useState(initial?.voiceId ?? "");
  const [promptLock, setPromptLock] = useState(initial?.promptLock ?? "");
  const [personality, setPersonality] = useState(initial?.memory.personality ?? "");
  const [catchphrases, setCatchphrases] = useState((initial?.memory.catchphrases ?? []).join("\n"));
  const [habits, setHabits] = useState((initial?.memory.habits ?? []).join("\n"));
  const [events, setEvents] = useState((initial?.memory.pastEventsSummary ?? []).join("\n"));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const idValid = /^[A-Za-z0-9_-]+$/.test(id);
  const canSave = name.trim() !== "" && (!isNew || idValid) && !busy;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSave) return;
    setBusy(true);
    setError("");
    try {
      await onSave(
        {
          id: initial?.id ?? id,
          projectId,
          name: name.trim(),
          role,
          heightCm: Number(heightCm) || 0,
          scaleRatio: Number(scaleRatio) || 1,
          voiceId: voiceId.trim(),
          description,
          defaultTempo: Number(tempo) || 1,
          promptLock,
          referenceImages: initial?.referenceImages ?? [],
          memory: {
            personality,
            catchphrases: lines(catchphrases),
            habits: lines(habits),
            pastEventsSummary: lines(events),
          },
        },
        isNew
      );
      onClose();
    } catch (err) {
      setError(t("error", { message: err instanceof Error ? err.message : String(err) }));
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <form
        role="dialog"
        aria-modal="true"
        aria-label={isNew ? t("createTitle") : t("editTitle")}
        onSubmit={submit}
        className="max-h-full w-full max-w-xl space-y-3 overflow-y-auto rounded-lg border border-border bg-card p-5"
      >
        <h2 className="text-base font-semibold text-foreground">
          {isNew ? t("createTitle") : t("editTitle")}
        </h2>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label={t("fId")}>
            <input className={inputCls} value={id} disabled={!isNew} onChange={(e) => setId(e.target.value)} placeholder="soc_nho" />
          </Field>
          <Field label={t("fName")}>
            <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label={t("fRole")}>
            <select className={inputCls} value={role} onChange={(e) => setRole(e.target.value as Character["role"])}>
              <option value="main">{t("roleMain")}</option>
              <option value="supporting">{t("roleSupporting")}</option>
            </select>
          </Field>
          <Field label={t("fVoice")}>
            <input className={inputCls} value={voiceId} onChange={(e) => setVoiceId(e.target.value)} />
          </Field>
          <Field label={t("fHeight")}>
            <input className={inputCls} type="number" min={1} value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
          </Field>
          <Field label={t("fScale")}>
            <input className={inputCls} type="number" step="0.1" min={0.1} value={scaleRatio} onChange={(e) => setScaleRatio(e.target.value)} />
          </Field>
        </div>

        <Field label={t("fTempo")}>
          <input className={inputCls} type="number" step="0.05" min={0.5} max={2} value={tempo} onChange={(e) => setTempo(e.target.value)} />
        </Field>
        <Field label={t("fDescription")}>
          <textarea className={inputCls} rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <Field label={t("fPrompt")}>
          <textarea className={inputCls} rows={3} value={promptLock} onChange={(e) => setPromptLock(e.target.value)} />
        </Field>
        <Field label={t("fPersonality")}>
          <input className={inputCls} value={personality} onChange={(e) => setPersonality(e.target.value)} />
        </Field>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Field label={t("fCatch")}>
            <textarea className={inputCls} rows={3} value={catchphrases} onChange={(e) => setCatchphrases(e.target.value)} />
          </Field>
          <Field label={t("fHabits")}>
            <textarea className={inputCls} rows={3} value={habits} onChange={(e) => setHabits(e.target.value)} />
          </Field>
          <Field label={t("fEvents")}>
            <textarea className={inputCls} rows={3} value={events} onChange={(e) => setEvents(e.target.value)} />
          </Field>
        </div>

        {error && <p className="text-[13px] text-semantic-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            {t("cancel")}
          </Button>
          <Button type="submit" size="sm" disabled={!canSave}>
            {t("save")}
          </Button>
        </div>
      </form>
    </div>
  );
}
