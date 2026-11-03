"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import type { ScheduledPost } from "@/lib/repositories/types";
import { CORE_URL } from "@/lib/repositories/core";
import { Plus, Check } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export function PublishTab() {
  const t = useTranslations("publishTab");
  const c = useTranslations("common");
  const {
    activeProjectId,
    channels,
    scheduledPosts,
    addScheduledPost,
    updateScheduledPost,
    episodes,
  } = useStudioStore();

  const [confirmPost, setConfirmPost] = useState<ScheduledPost | null>(null);
  const [creating, setCreating] = useState(false);
  const [newPlatform, setNewPlatform] = useState<"youtube" | "tiktok">(
    "youtube"
  );
  const [newTime, setNewTime] = useState("19:00");
  const [newEpTitle, setNewEpTitle] = useState(
    episodes[0]?.title || "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu"
  );

  const handleAddSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    const ch =
      channels.find((x) => x.platform === newPlatform) || channels[0];
    const post: ScheduledPost = {
      id: `sched_${Date.now().toString(36)}`,
      projectId: activeProjectId,
      episodeId: episodes[0]?.id || "ep_01_rang_sau",
      episodeTitle: newEpTitle,
      channelId: ch?.id || `ch_${newPlatform}`,
      channelName: ch?.name || `${newPlatform.toUpperCase()} Sóc Nhỏ TV`,
      platform: newPlatform,
      scheduledAt: `Hàng ngày · ${newTime}`,
      status: "pending_approval",
      manualApprovalRequired: true,
    };
    addScheduledPost(post);
    setCreating(false);
    try {
      await fetch(`${CORE_URL}/projects/${activeProjectId}/publishing/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(post),
      });
    } catch {
      // stored in Zustand
    }
  };

  const handleConfirmApprove = async () => {
    if (!confirmPost) return;
    const nextStatus =
      confirmPost.status === "pending_approval" ? "approved" : "published";
    updateScheduledPost(confirmPost.id, { status: nextStatus });
    try {
      await fetch(
        `${CORE_URL}/projects/${activeProjectId}/publishing/schedule/${confirmPost.id}/approve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus }),
        }
      );
    } catch {
      // stored in Zustand
    }
    setConfirmPost(null);
  };

  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Safety notice */}
      <div className="rounded-md border border-border bg-accent/50 p-2.5 text-[13px] text-foreground leading-snug">
        {t("manualApproveNote")}
      </div>

      {/* Connected channels */}
      <section className="space-y-2 border-b border-border pb-3.5">
        <h3 className="font-semibold text-foreground tnum">
          {t("channelsTitle", { count: channels.length })}
        </h3>
        <ul className="divide-y divide-border border-y border-border">
          {channels.map((ch) => (
            <li
              key={ch.id}
              className="flex items-center justify-between py-2"
            >
              <div>
                <p className="font-medium text-foreground">{ch.name}</p>
                <p className="text-[13px] text-muted-foreground uppercase">
                  {ch.platform} · {ch.defaultPublishHours}
                </p>
              </div>
              <span
                className={cn(
                  "rounded px-1.5 py-0.5 text-[13px] font-medium",
                  ch.connected
                    ? "bg-semantic-success/15 text-semantic-success"
                    : "bg-accent text-muted-foreground"
                )}
              >
                {ch.connected ? "Đã kết nối" : "Chưa kết nối"}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Weekly schedule */}
      <section className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground">
            {t("scheduleTitle")}
          </h3>
          <button
            type="button"
            onClick={() => setCreating((v) => !v)}
            className="flex h-6 items-center gap-1 rounded border border-border bg-card px-2 text-[13px] font-medium text-foreground hover:bg-accent"
          >
            <Plus className="h-3 w-3" />
            <span>{t("newScheduleBtn")}</span>
          </button>
        </div>

        {creating && (
          <form
            onSubmit={handleAddSchedule}
            className="rounded-md border border-border bg-card p-2.5 space-y-2"
          >
            <input
              type="text"
              value={newEpTitle}
              onChange={(e) => setNewEpTitle(e.target.value)}
              className="h-7 w-full rounded border border-border bg-background px-2 text-xs text-foreground"
            />
            <div className="grid grid-cols-2 gap-2">
              <select
                value={newPlatform}
                onChange={(e) =>
                  setNewPlatform(e.target.value as "youtube" | "tiktok")
                }
                className="h-7 rounded border border-border bg-background px-2 text-xs text-foreground"
              >
                <option value="youtube">YouTube</option>
                <option value="tiktok">TikTok</option>
              </select>
              <input
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="h-7 rounded border border-border bg-background px-2 text-xs tnum text-foreground"
              />
            </div>
            <div className="flex justify-end gap-1.5">
              <button
                type="button"
                onClick={() => setCreating(false)}
                className="h-6 rounded border border-border px-2 text-[13px] text-muted-foreground"
              >
                {c("cancel")}
              </button>
              <button
                type="submit"
                className="h-6 rounded bg-primary px-2.5 text-[13px] font-medium text-primary-foreground"
              >
                {c("create")}
              </button>
            </div>
          </form>
        )}

        <ul className="space-y-2">
          {scheduledPosts.map((post) => (
            <li
              key={post.id}
              className="rounded-md border border-border bg-card p-2.5 space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">
                    {post.episodeTitle}
                  </p>
                  <p className="text-[13px] text-muted-foreground tnum">
                    {post.channelName} ({post.platform.toUpperCase()}) ·{" "}
                    {post.scheduledAt}
                  </p>
                </div>
                <span
                  className={cn(
                    "shrink-0 rounded px-1.5 py-0.5 text-xs font-medium",
                    post.status === "approved" || post.status === "published"
                      ? "bg-semantic-success/15 text-semantic-success"
                      : "bg-accent text-foreground"
                  )}
                >
                  {t(`status.${post.status}` as any)}
                </span>
              </div>

              {post.status !== "published" && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => setConfirmPost(post)}
                    className="inline-flex h-6 items-center gap-1 rounded border border-border bg-card px-2 text-[13px] font-medium text-foreground hover:bg-accent"
                  >
                    <Check className="h-3 w-3" />
                    <span>
                      {post.status === "pending_approval"
                        ? t("approveBtn")
                        : t("publishNowBtn")}
                    </span>
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Manual approval confirmation dialog */}
      {confirmPost && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 p-4"
        >
          <div className="w-full max-w-sm rounded-lg border border-border bg-popover p-4 text-popover-foreground space-y-3">
            <h4 className="text-sm font-semibold">{t("approveConfirmTitle")}</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {t("approveConfirmDesc", {
                title: confirmPost.episodeTitle,
                platform: confirmPost.platform.toUpperCase(),
                time: confirmPost.scheduledAt,
              })}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmPost(null)}
                className="h-7 rounded border border-border px-2.5 text-xs text-foreground"
              >
                {c("cancel")}
              </button>
              <button
                type="button"
                onClick={handleConfirmApprove}
                className="h-7 rounded bg-primary px-2.5 text-xs font-medium text-primary-foreground"
              >
                {c("confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
