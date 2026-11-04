"use client";

import React, { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { X, Upload, Link2, AlertTriangle } from "@/components/ui/icons";
import { ingestFile, ingestUrls, type RightsType } from "@/lib/api/sources";

interface AddSourcesModalProps {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddSourcesModal({ projectId, onClose, onSuccess }: AddSourcesModalProps) {
  const t = useTranslations("sources");
  const [urlsText, setUrlsText] = useState("");
  const [rights, setRights] = useState<RightsType>("reference_only");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUrlsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const urls = urlsText
      .split("\n")
      .map((u) => u.trim())
      .filter(Boolean);

    if (urls.length === 0) {
      setError("Vui lòng dán ít nhất 1 liên kết video hợp lệ.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await ingestUrls(projectId, urls, rights, note);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Lỗi nạp liên kết");
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSubmitting(true);
    setError(null);
    try {
      await ingestFile(projectId, file, "owned", "Tập tin tải lên từ máy cá nhân");
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Lỗi tải lên video");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <h2 className="text-base font-semibold text-foreground">{t("addSource")}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-lg bg-rose-500/10 p-3 text-xs text-rose-500">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleUrlsSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-foreground">
              {t("pasteLinks")}
            </label>
            <textarea
              rows={4}
              value={urlsText}
              onChange={(e) => setUrlsText(e.target.value)}
              placeholder="https://v.douyin.com/...\nhttps://www.tiktok.com/@user/video/...\nhttps://www.youtube.com/shorts/..."
              className="mt-1.5 w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <p className="mt-1 text-[11px] text-muted-foreground">{t("pasteLinksHint")}</p>
          </div>

          {/* Rights notice */}
          <div className="rounded-xl border border-border/80 bg-background/60 p-3 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Lưu ý bản quyền:</span> {t("rightsNotice")}
          </div>

          <div className="flex items-center justify-between pt-2">
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                disabled={submitting}
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 rounded-xl border border-border px-3 py-2 text-xs font-medium text-foreground hover:bg-accent"
              >
                <Upload className="h-3.5 w-3.5" />
                {t("uploadLocal")}
              </button>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                {submitting ? "Đang xử lý..." : "Nạp nguồn"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
