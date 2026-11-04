"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { TemplateCard } from "@/components/templates/TemplateCard";
import { videoApi, type TemplateMeta } from "@/lib/api/video";
import { useVideoStore } from "@/store/modules/video";
import { Film, Search, Plus, Sparkles } from "@/components/ui/icons";

const CATEGORIES = [
  { id: "all", label: "Tất cả" },
  { id: "sales", label: "Bán hàng" },
  { id: "review", label: "Review KOC" },
  { id: "affiliate", label: "Affiliate" },
  { id: "reup", label: "Bản địa hoá" },
  { id: "animation", label: "Hoạt hình YT" },
  { id: "education", label: "Giáo dục" },
  { id: "story", label: "Truyện thiếu nhi" },
];

const PLATFORMS = ["all", "tiktok", "reels", "shorts", "youtube", "facebook", "douyin"];

export default function TemplatesPage() {
  const t = useTranslations("video");
  const {
    templates,
    setTemplates,
    selectedCategory,
    setSelectedCategory,
    selectedPlatform,
    setSelectedPlatform,
    searchQuery,
    setSearchQuery,
    loading,
    setLoading,
  } = useVideoStore();

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const data = await videoApi.fetchTemplates();
        if (isMounted) setTemplates(data);
      } catch (err) {
        console.error("Lỗi tải danh sách template:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [setTemplates, setLoading]);

  // Lọc templates
  const filteredTemplates = templates.filter((tpl) => {
    const matchCategory =
      selectedCategory === "all" || tpl.category.toLowerCase() === selectedCategory.toLowerCase();
    const matchPlatform =
      selectedPlatform === "all" ||
      tpl.platforms.map((p) => p.toLowerCase()).includes(selectedPlatform.toLowerCase());
    const matchSearch =
      !searchQuery.trim() ||
      tpl.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tpl.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchPlatform && matchSearch;
  });

  return (
    <div className="relative h-full w-full overflow-clip bg-slate-950 text-slate-100">
      <PageBar page="templates" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-7xl space-y-6 px-4 pb-12 pt-16 md:px-8">
          {/* Header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <Film className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white">{t("templates")}</h1>
                <p className="text-xs text-slate-400">{t("description")}</p>
              </div>
            </div>

            {/* Search input */}
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder={t("search")}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-900/90 pl-9 pr-3.5 py-2 text-xs text-slate-200 outline-none transition-colors placeholder:text-slate-500 focus:border-sky-500"
              />
            </div>
          </div>

          {/* Filters: Category & Platform */}
          <div className="flex flex-col gap-3">
            {/* Category Chips */}
            <div className="flex flex-wrap items-center gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`rounded-full px-3.5 py-1 text-xs font-semibold transition-all ${
                    selectedCategory === cat.id
                      ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                      : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Platform Filter */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
              <span className="font-medium mr-1">Nền tảng:</span>
              {PLATFORMS.map((plat) => (
                <button
                  key={plat}
                  type="button"
                  onClick={() => setSelectedPlatform(plat)}
                  className={`rounded-lg px-2.5 py-0.5 uppercase text-[11px] font-medium transition-colors ${
                    selectedPlatform === plat
                      ? "bg-slate-200 text-slate-950 font-bold"
                      : "bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800/80"
                  }`}
                >
                  {plat}
                </button>
              ))}
            </div>
          </div>

          {/* Template Grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-4">
            {filteredTemplates.map((tpl) => (
              <TemplateCard key={tpl.id} template={tpl} />
            ))}

            {/* Nút thêm = thẻ nét đứt cạnh thẻ cuối */}
            <div className="flex aspect-[9/16] flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-slate-800/80 bg-slate-950/40 p-4 text-center transition-all hover:border-sky-500/50 hover:bg-slate-900/30">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-slate-400">
                <Plus className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-300">Tạo mẫu mới</p>
                <p className="text-[10px] text-slate-500">Thêm template tùy chỉnh</p>
              </div>
            </div>
          </div>

          {filteredTemplates.length === 0 && !loading && (
            <div className="py-16 text-center text-sm text-slate-500">
              {t("noTemplates")}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
