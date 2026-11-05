"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { enterOnce } from "@/lib/motion";
import {
  Film,
  Sparkles,
  Search,
  X,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Plus,
  RefreshCw,
  Layers,
} from "@/components/ui/icons";
import { TemplateV2Card, type TemplateV2Data } from "./TemplateV2Card";
import { TemplateDetailDrawer } from "./TemplateDetailDrawer";
import { usePreview } from "@/lib/preview";
import { AiLoading } from "@/components/ui/AiLoading";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { confirm } from "@/lib/confirm";
import { useStudioStore } from "@/store";
import { generateTemplateGraph } from "@/lib/template-graphs";
import { useRouter } from "@/i18n/routing";

const EASE = [0.22, 1, 0.36, 1] as const;

const KIND_TABS = [
  { id: "all", label: "Tất cả mẫu" },
  { id: "koc", label: "TikTok KOC" },
  { id: "review", label: "Review & Đập hộp" },
  { id: "animation", label: "Hoạt hình" },
  { id: "remotion-style", label: "Motion Graphics" },
  { id: "handdrawn", label: "Vẽ tay (Whiteboard)" },
  { id: "replace", label: "Thay nhân vật" },
  { id: "fact", label: "Shorts Facts" },
  { id: "reup", label: "Bản địa hoá" },
];

const TIER_FILTERS = [
  { id: "all", label: "Mọi Tier" },
  { id: "A", label: "Tier A (Offline)" },
  { id: "B", label: "Tier B (Cloud AI)" },
  { id: "C", label: "Tier C (GPU)" },
];

export function TemplatesView({ className }: { className?: string }) {
  const router = useRouter();
  const { activeProjectId, setNodesAndEdges } = useStudioStore();
  const [templates, setTemplates] = useState<TemplateV2Data[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [activeKind, setActiveKind] = useState("all");
  const [activeTier, setActiveTier] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/templates");
      const data = await res.json();
      if (data.ok && Array.isArray(data.templates)) {
        setTemplates(data.templates);
      } else {
        setError(data.error || "Không thể tải danh sách template");
      }
    } catch (err: any) {
      setError(err.message || "Lỗi mạng khi tải template");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const filtered = useMemo(() => {
    return templates.filter((t) => {
      // 1. Kind tab
      if (activeKind !== "all") {
        if (activeKind === "koc" && t.kind !== "koc" && t.category !== "sales") return false;
        if (activeKind === "review" && t.kind !== "review" && t.category !== "affiliate") return false;
        if (activeKind === "animation" && t.kind !== "animation") return false;
        if (activeKind === "remotion-style" && t.kind !== "remotion-style") return false;
        if (activeKind === "handdrawn" && t.kind !== "handdrawn") return false;
        if (activeKind === "replace" && t.kind !== "replace") return false;
        if (activeKind === "fact" && t.kind !== "fact" && t.category !== "education") return false;
        if (activeKind === "reup" && t.kind !== "reup") return false;
      }
      // 2. Tier filter
      if (activeTier !== "all" && t.tier !== activeTier) return false;
      // 3. Search query
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchName = t.name.toLowerCase().includes(q);
        const matchKind = t.kind.toLowerCase().includes(q);
        const matchCat = t.category.toLowerCase().includes(q);
        const matchId = t.id.toLowerCase().includes(q);
        if (!matchName && !matchKind && !matchCat && !matchId) return false;
      }
      return true;
    });
  }, [templates, activeKind, activeTier, search]);

  const handleSelectTemplate = (template: TemplateV2Data) => {
    setSelectedId(template.id);
    usePreview.getState().open({
      kind: "custom",
      title: template.name,
      render: (close) => <TemplateDetailDrawer template={template} onClose={close} />,
    });
  };

  const handleDoubleApply = async (template: TemplateV2Data) => {
    setSelectedId(template.id);
    const confirmed = await confirm({
      tone: "info",
      title: `Dựng đồ thị từ mẫu: ${template.name}`,
      message: `Đồ thị Studio sẽ được khởi tạo với ${template.recipe?.nodes?.length || 5} node liên kết theo đúng cấu trúc của mẫu này. Bạn có muốn tiếp tục?`,
      confirmLabel: "Dựng đồ thị",
      cancelLabel: "Hủy",
    });

    if (confirmed) {
      const bundle = generateTemplateGraph({
        projectId: activeProjectId || "soc-nho-tv",
        template: template as any,
        topic: template.name,
      });

      if (bundle.reactFlowGraph) {
        setNodesAndEdges(bundle.reactFlowGraph.nodes as any, bundle.reactFlowGraph.edges as any);
      }
      usePreview.getState().close();
      router.push("/studio");
    }
  };

  return (
    <div className={cn("flex h-full w-full flex-col overflow-hidden text-left bg-background select-none", className)}>
      {/* Thanh Tiêu Đề & Bộ Lọc Nhanh */}
      <div className="shrink-0 border-b border-border bg-card/40 px-5 py-3.5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Film className="h-5 w-5 text-primary" />
              <h1 className="text-base font-bold text-foreground">
                Thư Viện Mẫu Video (HyperFrames Studio)
              </h1>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground tnum">
                {filtered.length}/{templates.length}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Mỗi mẫu xuất ra video MP4 thật theo chuẩn Safe Zone và TikTok mastering -14 LUFS.
            </p>
          </div>

          {/* Ô Tìm Kiếm */}
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Tìm mẫu, định dạng..."
                className="h-8 w-full rounded-xl border border-border bg-background pl-8 pr-7 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-foreground/40 transition-colors"
              />
              {search && (
                <button
                  type="button"
                  title="Xóa tìm kiếm"
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {/* Nút Làm Mới */}
            <button
              type="button"
              title="Tải lại danh sách"
              aria-label="Tải lại danh sách"
              onClick={fetchTemplates}
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-border text-muted-foreground hover:bg-accent hover:text-foreground active:scale-95 transition-colors"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            </button>
          </div>
        </div>

        {/* Tab Chủng Loại (Căn trái - Quy tắc UI 5) */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/50">
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {KIND_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveKind(tab.id)}
                className={cn(
                  "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                  activeKind === tab.id
                    ? "bg-foreground text-background shadow-xs font-semibold"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Lọc Theo Tier */}
          <div className="flex items-center gap-1 text-[11px]">
            {TIER_FILTERS.map((tf) => (
              <button
                key={tf.id}
                type="button"
                onClick={() => setActiveTier(tf.id)}
                className={cn(
                  "rounded-md border px-2 py-0.5 font-medium transition-colors",
                  activeTier === tf.id
                    ? "border-foreground bg-accent text-foreground font-semibold"
                    : "border-border text-muted-foreground hover:bg-muted"
                )}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Lưới Danh Sách Thẻ Mẫu */}
      <div className="flex-1 overflow-y-auto scroll-quiet p-5">
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <AiLoading label="Đang nạp thư viện template..." />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center text-muted-foreground">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <p className="text-sm font-semibold text-foreground">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchTemplates}>
              Thử lại
            </Button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-center text-muted-foreground">
            <Film className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm font-medium">Không tìm thấy mẫu nào phù hợp với bộ lọc.</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActiveKind("all");
                setActiveTier("all");
                setSearch("");
              }}
            >
              Đặt lại bộ lọc
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
            {filtered.map((t) => (
              <TemplateV2Card
                key={t.id}
                template={t}
                isSelected={selectedId === t.id}
                onClick={() => handleSelectTemplate(t)}
                onDoubleClick={() => handleDoubleApply(t)}
              />
            ))}

            {/* Ô Viền Nét Đứt Gợi Ý Thêm / Tạo Mẫu Mới (Quy tắc UI 20, 22) */}
            <div
              role="button"
              tabIndex={0}
              title="Tạo template mới theo kịch bản tùy biến"
              aria-label="Tạo template mới"
              onClick={() => {
                confirm({
                  tone: "info",
                  title: "Khởi tạo Template Mới",
                  message: "Mở trình soạn thảo tạo template mới với Jinja2 composition và CSS custom.",
                  confirmLabel: "Vào Studio tạo đồ thị mẫu",
                }).then((ok) => {
                  if (ok) router.push("/studio");
                });
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") router.push("/studio");
              }}
              className="flex aspect-[9/16] flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-border p-4 text-center text-muted-foreground hover:border-foreground/40 hover:bg-accent/20 hover:text-foreground cursor-pointer transition-all active:scale-98"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-dashed border-border bg-muted/60">
                <Plus className="h-5 w-5" />
              </div>
              <span className="text-xs font-bold text-foreground">Tạo template mới</span>
              <span className="text-[10px] text-muted-foreground line-clamp-2">
                Dựng kịch bản tùy biến và lưu thành mẫu mới
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
