"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Plus,
  RefreshCw,
  Trash2,
  Bookmark,
  Copy,
  Tag,
  CheckCircle,
  X,
  AlertCircle,
} from "@/components/ui/icons";
import { ContentTemplate, PlatformType } from "@/lib/api/social";

interface TemplatesViewProps {
  onUseTemplate?: (tmpl: ContentTemplate) => void;
}

const PURPOSES = [
  { id: "all", label: "Tất cả mục đích" },
  { id: "sales", label: "Bán hàng (Sales)" },
  { id: "koc", label: "KOC Review" },
  { id: "education", label: "Giáo dục / Kỹ năng" },
  { id: "story", label: "Kể chuyện / Phim" },
];

export function TemplatesView({ onUseTemplate }: TemplatesViewProps) {
  const { activeProjectId } = useStudioStore();
  const { templates, loadTemplates, loading: isLoadingTemplates } = useSocialStore();

  const [purposeFilter, setPurposeFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ContentTemplate | null>(null);

  // Form State
  const [formTitle, setFormTitle] = useState("");
  const [formPurpose, setFormPurpose] = useState("sales");
  const [formPlatform, setFormPlatform] = useState<PlatformType | "all">("all");
  const [formCaption, setFormCaption] = useState("");
  const [formHashtags, setFormHashtags] = useState("");
  const [formFirstComment, setFormFirstComment] = useState("");
  const [formCta, setFormCta] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (activeProjectId) {
      loadTemplates(activeProjectId);
    }
  }, [activeProjectId, loadTemplates]);

  const filteredTemplates = templates.filter((t) => {
    if (purposeFilter !== "all" && t.purpose !== purposeFilter) return false;
    if (platformFilter !== "all" && !t.platforms?.includes(platformFilter as any)) return false;
    return true;
  });

  const handleOpenAdd = () => {
    setEditingTemplate(null);
    setFormTitle("");
    setFormPurpose("sales");
    setFormPlatform("all");
    setFormCaption("{title}\n\n👉 Khám phá ngay cùng Sóc Nhỏ!\n{cta}");
    setFormHashtags("socnhotv, hoathinh3d, hocdieuhay");
    setFormFirstComment("");
    setFormCta("Link chi tiết để dưới phần bình luận nha cả nhà!");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (t: ContentTemplate) => {
    setEditingTemplate(t);
    setFormTitle(t.name || t.title || "");
    setFormPurpose(t.purpose || "sales");
    setFormPlatform(t.platforms?.[0] || "all");
    setFormCaption(t.caption_template || t.caption_body || "");
    setFormHashtags(t.hashtags?.join(", ") || "");
    setFormFirstComment(t.first_comment || "");
    setFormCta(t.caption_cta || t.cta || "");
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProjectId || !formTitle.trim()) return;

    setSaving(true);
    try {
      const hashtagsArray = formHashtags
        .split(/[, ]+/)
        .map((h) => h.trim().replace(/^#/, ""))
        .filter(Boolean);

      const payload = {
        title: formTitle.trim(),
        purpose: formPurpose,
        platform: formPlatform,
        caption_template: formCaption,
        hashtags: hashtagsArray,
        first_comment: formFirstComment,
        cta: formCta,
      };

      const url = editingTemplate
        ? `/core/projects/${activeProjectId}/social/templates/${editingTemplate.id}`
        : `/core/projects/${activeProjectId}/social/templates`;
      const method = editingTemplate ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setIsModalOpen(false);
        loadTemplates(activeProjectId);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (tmplId: string, title: string) => {
    if (!activeProjectId) return;
    if (!confirm(`Bạn có chắc muốn xóa mẫu "${title}"?`)) return;

    try {
      const res = await fetch(`/core/projects/${activeProjectId}/social/templates/${tmplId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        loadTemplates(activeProjectId);
      }
    } catch {
      // Ignore
    }
  };

  const handleCopyCaption = (t: ContentTemplate) => {
    const caption = t.caption_template || t.caption_body || "";
    const fullText = `${caption}\n\n${(t.hashtags || []).map((h) => `#${h}`).join(" ")}`;
    navigator.clipboard.writeText(fullText);
    setCopiedId(t.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border">
        <div>
          <h2 className="text-base font-bold text-foreground">Kho Mẫu Nội Dung & Caption</h2>
          <p className="text-xs text-muted-foreground mt-1">
            Mẫu caption, hashtag, lời kêu gọi (CTA) theo mục đích bán hàng, KOC review hoặc giáo dục
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground font-medium text-xs hover:bg-primary/90 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Tạo mẫu mới
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-2 border-b border-border pb-3">
        <div className="flex items-center gap-1 overflow-x-auto">
          {PURPOSES.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPurposeFilter(p.id)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap",
                purposeFilter === p.id
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {p.label}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => activeProjectId && loadTemplates(activeProjectId)}
          className="p-1.5 rounded-lg border border-border bg-background text-muted-foreground hover:text-foreground"
          aria-label="Tải lại mẫu"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isLoadingTemplates && "animate-spin")} />
        </button>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((t) => (
          <div
            key={t.id}
            className="flex flex-col justify-between p-4 rounded-xl border border-border bg-card hover:border-border/80 transition-all space-y-3"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-xs md:text-sm text-foreground line-clamp-1">
                  {t.name || t.title}
                </h3>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/50 shrink-0">
                  {t.purpose || "chung"}
                </span>
              </div>

              {/* Caption preview */}
              <p className="text-xs text-muted-foreground line-clamp-4 mt-2.5 whitespace-pre-wrap leading-relaxed font-sans bg-muted/30 p-2.5 rounded-lg border border-border/40">
                {t.caption_template || t.caption_body}
              </p>

              {/* Hashtags */}
              {t.hashtags && t.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2.5">
                  {t.hashtags.map((h, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] text-primary bg-primary/10 px-1.5 py-0.2 rounded font-mono"
                    >
                      #{h}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions Footer */}
            <div className="flex items-center justify-between pt-2.5 border-t border-border/50 text-xs">
              <button
                type="button"
                onClick={() => handleCopyCaption(t)}
                className="text-primary hover:underline flex items-center gap-1 font-medium"
              >
                {copiedId === t.id ? (
                  <>
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Đã chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao chép</span>
                  </>
                )}
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleOpenEdit(t)}
                  className="text-muted-foreground hover:text-foreground text-xs"
                >
                  Sửa
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(t.id, t.name || t.title || "mẫu")}
                  className="text-destructive hover:underline p-1"
                  aria-label="Xóa mẫu"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl bg-card border border-border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
              <h3 className="font-semibold text-sm text-foreground">
                {editingTemplate ? "Chỉnh sửa Mẫu Nội Dung" : "Tạo Mẫu Nội Dung Mới"}
              </h3>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="p-5 space-y-4 text-xs">
              <div>
                <label className="font-semibold text-foreground block mb-1">Tên mẫu</label>
                <input
                  type="text"
                  required
                  placeholder="VD: Mẫu bán hàng SunShield"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-foreground block mb-1">Mục đích</label>
                  <select
                    value={formPurpose}
                    onChange={(e) => setFormPurpose(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground focus:outline-none"
                  >
                    <option value="sales">Bán hàng (Sales)</option>
                    <option value="koc">KOC Review</option>
                    <option value="education">Giáo dục / Kỹ năng</option>
                    <option value="story">Kể chuyện / Phim</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-foreground block mb-1">Nền tảng phù hợp</label>
                  <select
                    value={formPlatform}
                    onChange={(e) => setFormPlatform(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground focus:outline-none"
                  >
                    <option value="all">Tất cả nền tảng</option>
                    <option value="youtube">YouTube</option>
                    <option value="tiktok">TikTok</option>
                    <option value="facebook">Facebook</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-foreground block mb-1">
                  Nội dung Caption mẫu
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Nhập nội dung mẫu..."
                  value={formCaption}
                  onChange={(e) => setFormCaption(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none font-sans leading-relaxed"
                />
              </div>

              <div>
                <label className="font-semibold text-foreground block mb-1">Hashtags (phân tách bởi dấu phẩy)</label>
                <input
                  type="text"
                  placeholder="socnhotv, hoathinh3d, hocdieuhay"
                  value={formHashtags}
                  onChange={(e) => setFormHashtags(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground font-mono placeholder:text-muted-foreground focus:outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-foreground block mb-1">Lời kêu gọi (CTA)</label>
                <input
                  type="text"
                  placeholder="Bấm ngay vào giỏ hàng bên dưới để nhận ưu đãi!"
                  value={formCta}
                  onChange={(e) => setFormCta(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-border bg-background text-foreground hover:bg-muted font-medium"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {saving ? "Đang lưu..." : editingTemplate ? "Lưu thay đổi" : "Tạo mẫu"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
