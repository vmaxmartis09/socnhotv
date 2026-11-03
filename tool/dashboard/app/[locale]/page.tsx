"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import {
  getRepository,
  type Project,
  type Channel,
  type Character,
} from "@/lib/repositories";
import { useStudioStore } from "@/store";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const PLATFORM_LABEL: Record<Channel["platform"], string> = {
  youtube: "YouTube",
  tiktok: "TikTok",
  facebook: "Facebook",
  instagram: "Instagram",
  x: "X",
};

/** Height lock drawn to one shared cm scale: the rule that keeps every scene in proportion. */
function ScaleLock({ characters }: { characters: Character[] }) {
  const t = useTranslations("overview");
  const tallest = Math.max(...characters.map((c) => c.heightCm), 1);
  const H = 132;
  return (
    <figure aria-label={t("scaleLock")} className="min-w-0">
      <figcaption className="mb-3 text-sm font-medium">{t("scaleLock")}</figcaption>
      <div className="flex items-end gap-6 border-b border-border">
        {characters.map((c, i) => {
          const h = Math.round((c.heightCm / tallest) * H);
          return (
            <div key={c.id} className="flex flex-col items-center gap-1.5">
              <span className="text-xs tnum text-muted-foreground">
                {t("cm", { value: c.heightCm })}
              </span>
              <div
                style={{ height: h }}
                className={cn("w-9 rounded-t-[4px]", i === 0 ? "bg-brand" : "bg-brand/30")}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-1.5 flex gap-6">
        {characters.map((c) => (
          <span key={c.id} className="w-9 text-center text-xs text-muted-foreground">
            {c.name.replace(/\s*\(.*\)/, "").replace("Bạn ", "")}
          </span>
        ))}
      </div>
      <p className="mt-3 max-w-[22ch] text-xs leading-snug text-muted-foreground">{t("scaleLockNote")}</p>
    </figure>
  );
}

function Pill({ tone, children }: { tone: "positive" | "neutral"; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded-full px-2 text-xs font-medium",
        tone === "positive"
          ? "bg-semantic-success/12 text-semantic-success"
          : "bg-accent text-muted-foreground"
      )}
    >
      {children}
    </span>
  );
}

export default function DashboardOverviewPage() {
  const t = useTranslations("overview");
  const { activeProjectId, jobs } = useStudioStore();
  const [project, setProject] = useState<Project | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);

  useEffect(() => {
    async function load() {
      const repo = getRepository();
      setProject(await repo.getProject(activeProjectId));
      setChannels(await repo.listChannels());
      setCharacters(await repo.listCharacters(activeProjectId));
    }
    load();
  }, [activeProjectId]);

  const running = jobs.filter((j) => j.status === "running").length;
  const done = jobs.filter((j) => j.status === "completed").length;
  const finding =
    running > 0 ? t("findingBusy", { count: running }) : done > 0 ? t("findingDone", { count: done }) : t("findingEmpty");

  return (
    <div className="mx-auto max-w-[1100px] px-4 py-6 sm:px-6 md:px-8 md:py-8">
      {/* Title row: the screen's one question is "where do I pick up?", the finding answers it */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-[22px] font-semibold leading-tight tracking-tight">
            {project?.name ?? " "}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">{project?.description}</p>
          <p className="mt-3 text-sm text-foreground">{finding}</p>
          {project && (
            <p className="mt-1 text-xs tnum text-muted-foreground">
              {t("counts", {
                episodes: project.episodesCount,
                characters: project.charactersCount,
                channels: channels.length,
              })}
            </p>
          )}
        </div>
        <Link href="/studio" className="shrink-0">
          <Button>{t("openCanvas")}</Button>
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Characters as themselves: portrait, role, voice, height */}
        <section className="lg:col-span-7">
          <h2 className="mb-3 text-base font-medium">{t("characters")}</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-[1fr_auto]">
            <ul className="divide-y divide-border border-y border-border">
              {characters.map((c) => {
                const img = c.referenceImages[0];
                return (
                  <li key={c.id} className="flex items-center gap-3 py-3">
                    {img ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={img}
                        alt={c.name}
                        className="h-11 w-11 shrink-0 rounded-md bg-accent object-cover object-top"
                      />
                    ) : (
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-accent text-sm font-medium text-muted-foreground">
                        {c.name.replace("Bạn ", "").charAt(0)}
                      </span>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{c.name}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {c.role === "main" ? t("roleMain") : t("roleSupporting")} · {t("voice")}{" "}
                        <span className="font-mono">{c.voiceId}</span>
                      </p>
                    </div>
                    <span className="text-sm tnum text-muted-foreground">{t("cm", { value: c.heightCm })}</span>
                  </li>
                );
              })}
            </ul>
            {characters.length > 0 && <ScaleLock characters={characters} />}
          </div>
        </section>

        {/* Channels: a ruled table, numbers right-aligned */}
        <section className="lg:col-span-5">
          <h2 className="mb-3 text-base font-medium">{t("channels")}</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-y border-border text-left text-xs text-muted-foreground">
                <th className="py-2 pr-3 font-medium">{t("colChannel")}</th>
                <th className="py-2 pr-3 text-right font-medium">{t("colTime")}</th>
                <th className="py-2 text-right font-medium">{t("colState")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border border-b border-border">
              {channels.map((ch) => (
                <tr key={ch.id}>
                  <td className="py-3 pr-3">
                    <p className="truncate font-medium">{ch.name}</p>
                    <p className="text-xs text-muted-foreground">{PLATFORM_LABEL[ch.platform]}</p>
                  </td>
                  <td className="py-3 pr-3 text-right tnum">{ch.defaultPublishHours}</td>
                  <td className="py-3 text-right">
                    <Pill tone={ch.connected ? "positive" : "neutral"}>
                      {ch.connected ? t("connected") : t("notConnected")}
                    </Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Production standard: one ruled definition row, no cards */}
        <section className="lg:col-span-12">
          <h2 className="mb-3 text-base font-medium">{t("standards")}</h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 border-y border-border py-4 md:grid-cols-4">
            <div>
              <dt className="text-xs text-muted-foreground">{t("aspect")}</dt>
              <dd className="mt-1 text-sm tnum">{project?.defaultAspectRatio ?? "–"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">{t("defaultVoice")}</dt>
              <dd className="mt-1 font-mono text-sm">{project?.defaultVoiceId ?? "–"}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">{t("editor")}</dt>
              <dd className="mt-1 text-sm">HyperFrames</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">{t("platforms")}</dt>
              <dd className="mt-1 text-sm">
                {project?.targetPlatforms.map((p) => PLATFORM_LABEL[p]).join(", ") ?? "–"}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
