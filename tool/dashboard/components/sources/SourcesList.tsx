"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Plus, Search, Database, RotateCcw } from "@/components/ui/icons";
import { confirm } from "@/lib/confirm";
import { useSourcesStore } from "@/store/modules/sources";
import type { SourceItem } from "@/lib/api/sources";
import { deleteSource, listSources } from "@/lib/api/sources";
import { SourceCard } from "./SourceCard";
import { SourceDetailModal } from "./SourceDetailModal";
import { AddSourcesModal } from "./AddSourcesModal";

export function SourcesList({ projectId }: { projectId: string }) {
  const t = useTranslations("sources");
  const {
    sources,
    setSources,
    activeSource,
    setActiveSource,
    loading,
    setLoading,
    filterPlatform,
    setFilterPlatform,
    filterRights,
    setFilterRights,
    searchQuery,
    setSearchQuery,
    removeSource,
  } = useSourcesStore();

  const [addModalOpen, setAddModalOpen] = useState(false);

  const fetchSources = async () => {
    setLoading(true);
    try {
      const data = await listSources(projectId, {
        platform: filterPlatform || undefined,
        rights: filterRights || undefined,
        q: searchQuery || undefined,
      });
      setSources(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [projectId, filterPlatform, filterRights, searchQuery]);

  const handleDelete = async (sourceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const ok = await confirm({
      title: "Chuyển nguồn vào thùng rác",
      message: t("confirmTrash"),
      tone: "danger",
      confirmLabel: "Chuyển vào thùng rác",
      cancelLabel: "Hủy",
    });
    if (!ok) return;

    try {
      await deleteSource(projectId, sourceId);
      removeSource(sourceId);
    } catch (err: any) {
      alert(err.message || "Lỗi xóa nguồn");
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-card p-3 shadow-sm">
        <div className="flex flex-1 flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative min-w-[200px] flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("search")}
              className="h-8 w-full rounded-lg border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Filter Platform */}
          <select
            value={filterPlatform}
            onChange={(e) => setFilterPlatform(e.target.value)}
            className="h-8 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground focus:outline-none"
          >
            <option value="">{t("filterAll")}</option>
            <option value="douyin">Douyin</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
            <option value="bilibili">Bilibili</option>
            <option value="local">Local</option>
          </select>

          {/* Filter Rights */}
          <select
            value={filterRights}
            onChange={(e) => setFilterRights(e.target.value)}
            className="h-8 rounded-lg border border-border bg-background px-2.5 text-xs text-foreground focus:outline-none"
          >
            <option value="">{t("filterRightsAll")}</option>
            <option value="reference_only">{t("rights.reference_only")}</option>
            <option value="owned">{t("rights.owned")}</option>
            <option value="licensed">{t("rights.licensed")}</option>
            <option value="permission">{t("rights.permission")}</option>
          </select>
        </div>

        <button
          type="button"
          onClick={fetchSources}
          title="Tải lại"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <RotateCcw className={loading ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
        </button>
      </div>

      {/* Grid of Sources */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {sources.map((s) => (
          <SourceCard
            key={s.id}
            source={s}
            projectId={projectId}
            onSelect={setActiveSource}
            onDelete={handleDelete}
          />
        ))}

        {/* Dashed Add Card next to the last card */}
        <button
          type="button"
          onClick={() => setAddModalOpen(true)}
          className="group flex aspect-[9/16] max-h-[300px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-card/40 p-4 text-center transition-all hover:border-primary/60 hover:bg-card"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background transition-transform group-hover:scale-110">
            <Plus className="h-5 w-5 text-muted-foreground group-hover:text-primary" />
          </div>
          <span className="mt-3 text-xs font-semibold text-foreground group-hover:text-primary">
            {t("addSource")}
          </span>
          <span className="mt-1 text-[11px] text-muted-foreground">
            Dán link hoặc tải file
          </span>
        </button>
      </div>

      {sources.length === 0 && !loading && (
        <div className="rounded-2xl border border-dashed border-border p-12 text-center text-xs text-muted-foreground">
          {t("empty")}
        </div>
      )}

      {/* Modals */}
      {addModalOpen && (
        <AddSourcesModal
          projectId={projectId}
          onClose={() => setAddModalOpen(false)}
          onSuccess={fetchSources}
        />
      )}

      {activeSource && (
        <SourceDetailModal
          source={activeSource}
          projectId={projectId}
          onClose={() => setActiveSource(null)}
          onUpdated={(updated) => {
            setActiveSource(updated);
            setSources(sources.map((s) => (s.id === updated.id ? updated : s)));
          }}
        />
      )}
    </div>
  );
}
