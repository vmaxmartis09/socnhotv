"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";

export function JobsCostTab() {
  const t = useTranslations("jobsTab");
  const {
    jobs,
    totalSpentUsd,
    perRunSpendingLimitUsd,
    dailySpendingLimitUsd,
  } = useStudioStore();

  const activeJobs = jobs.filter(
    (j) => j.status === "running" || j.status === "queued"
  );
  const completedJobs = jobs.filter(
    (j) => j.status === "completed" || j.status === "failed"
  );

  const pctDaily = Math.min(
    100,
    Math.round((totalSpentUsd / Math.max(0.5, dailySpendingLimitUsd)) * 100)
  );

  return (
    <div className="p-3.5 space-y-4 text-xs">
      {/* Spending vs Ceilings */}
      <section className="rounded-md border border-border bg-card p-3 space-y-2">
        <h3 className="font-semibold text-foreground">{t("budgetTitle")}</h3>
        <div className="space-y-1 text-[11px] tnum">
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              {t("spentToday", { spent: totalSpentUsd.toFixed(2) })}
            </span>
            <span className="font-medium text-foreground">
              {t("dailyCeiling", { limit: dailySpendingLimitUsd.toFixed(2) })}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded bg-accent">
            <div
              style={{ width: `${pctDaily}%` }}
              className="h-full bg-brand transition-[width]"
            />
          </div>
          <p className="pt-1 text-muted-foreground">
            {t("perRunCeiling", { limit: perRunSpendingLimitUsd.toFixed(2) })}
          </p>
        </div>
      </section>

      {/* Active running queue */}
      <section className="space-y-2 border-b border-border pb-3.5">
        <h3 className="font-semibold text-foreground tnum">
          {t("activeQueueTitle", { count: activeJobs.length })}
        </h3>
        {activeJobs.length === 0 ? (
          <p className="text-[11px] text-muted-foreground">
            {t("noActiveJobs")}
          </p>
        ) : (
          <ul className="space-y-2">
            {activeJobs.map((j) => (
              <li
                key={j.id}
                className="rounded-md border border-brand bg-card p-2.5 space-y-1 tnum"
              >
                <div className="flex justify-between">
                  <span className="font-mono font-medium text-brand">
                    {j.id} ({j.type})
                  </span>
                  <span className="text-brand">{j.progress}%</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* History */}
      <section className="space-y-2">
        <h3 className="font-semibold text-foreground tnum">
          {t("historyTitle", { count: completedJobs.length })}
        </h3>
        {completedJobs.length === 0 ? (
          <p className="text-[11px] text-muted-foreground">{t("noHistory")}</p>
        ) : (
          <ul className="space-y-2">
            {completedJobs.map((j) => (
              <li
                key={j.id}
                className="rounded-md border border-border bg-card p-2.5 space-y-1 tnum"
              >
                <div className="flex justify-between">
                  <span className="font-mono text-foreground">{j.id}</span>
                  <span className="text-semantic-success">
                    ${(j.actualCostUsd ?? 0).toFixed(2)} USD
                  </span>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  {j.completedAt || j.createdAt}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
