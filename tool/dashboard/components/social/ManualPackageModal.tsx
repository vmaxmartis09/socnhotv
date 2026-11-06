"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { socialApi } from "@/lib/api/social";
import {
  X,
  Copy,
  Download,
  Check,
  CheckCircle2,
  ExternalLink,
  Film,
  Sparkles,
  RefreshCw,
  AlertCircle,
} from "@/components/ui/icons";

interface ManualPackageModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  post: {
    post_id: string;
    target_id: string;
    title: string;
    platform: string;
    caption?: string;
    hashtags?: string[];
    external_url?: string;
    status?: string;
  };
  onMarkPublished?: (postId: string, targetId: string, url: string) => Promise<void>;
}

export function ManualPackageModal({
  isOpen,
  onClose,
  projectId,
  post,
  onMarkPublished,
}: ManualPackageModalProps) {
  const [loading, setLoading] = useState(false);
  const [packageData, setPackageData] = useState<{
    caption: string;
    hashtags: string;
    checklist: string;
    zip_path: string | null;
    zip_filename: string | null;
    has_real_video: boolean;
  } | null>(null);

  const [copiedCaption, setCopiedCaption] = useState(false);
  const [copiedTags, setCopiedTags] = useState(false);
  const [showMarkInput, setShowMarkInput] = useState(false);
  const [postedUrl, setPostedUrl] = useState(post.external_url || "");
  const [marking, setMarking] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setErrorMsg(null);
    socialApi
      .getPackageInfo(projectId, post.post_id, post.platform)
      .then((data) => {
        setPackageData(data);
      })
      .catch((err) => {
        // If not found, try generate
        socialApi
          .generatePackage(projectId, post.post_id, post.platform)
          .then((data) => setPackageData(data))
          .catch((gErr) => setErrorMsg(gErr.message || "Không thể nạp gói đăng"));
      })
      .finally(() => setLoading(false));
  }, [isOpen, projectId, post.post_id, post.platform]);

  if (!isOpen) return null;

  const handleCopyCaption = () => {
    const text = packageData?.caption || post.caption || "";
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedCaption(true);
    setTimeout(() => setCopiedCaption(false), 2000);
  };

  const handleCopyTags = () => {
    const text = packageData?.hashtags || (post.hashtags ? post.hashtags.join(" ") : "");
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedTags(true);
    setTimeout(() => setCopiedTags(false), 2000);
  };

  const handleMarkPublishedConfirm = async () => {
    if (!postedUrl.trim()) {
      setErrorMsg("Vui lòng nhập link bài viết thật đã đăng trên " + post.platform.toUpperCase());
      return;
    }
    setMarking(true);
    setErrorMsg(null);
    try {
      if (onMarkPublished) {
        await onMarkPublished(post.post_id, post.target_id, postedUrl.trim());
      } else {
        await socialApi.markPublished(projectId, post.post_id, post.target_id, postedUrl.trim());
      }
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi cập nhật trạng thái");
    } finally {
      setMarking(false);
    }
  };

  const zipDownloadUrl = socialApi.getPackageZipUrl(projectId, post.post_id, post.platform);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-xl max-h-[90vh] flex flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden text-xs">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-muted/40">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Film className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-bold text-foreground text-sm leading-tight">
                Gói Đăng Thủ Công
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {post.platform.toUpperCase()} · {post.title}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Đóng"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 scroll-quiet">
          {errorMsg && (
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 text-xs">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-muted-foreground gap-2">
              <RefreshCw className="h-6 w-6 animate-spin text-primary" />
              <span>Đang chuẩn bị gói đăng...</span>
            </div>
          ) : (
            <>
              {/* ZIP Download Bar */}
              <div className="p-3.5 rounded-xl border border-border bg-gradient-to-r from-primary/5 via-card to-primary/10 flex items-center justify-between gap-3 shadow-2xs">
                <div className="space-y-0.5 min-w-0">
                  <div className="font-semibold text-foreground flex items-center gap-1.5">
                    <Download className="h-4 w-4 text-primary" />
                    <span>Tải gói xuất bản đầy đủ (.zip)</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground truncate">
                    Chứa video.mp4, cover.jpg, caption.txt, hashtags.txt, checklist.md
                  </p>
                </div>
                <a
                  href={zipDownloadUrl}
                  download={`${post.platform}_package_${post.post_id}.zip`}
                  className="px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-colors shrink-0 flex items-center gap-1.5 shadow-sm"
                >
                  <Download className="h-3.5 w-3.5" />
                  Tải ZIP
                </a>
              </div>

              {/* Caption Section */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                    Nội dung Caption
                  </span>
                  <button
                    type="button"
                    onClick={handleCopyCaption}
                    className="flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-muted text-primary text-[11px] transition-colors"
                  >
                    {copiedCaption ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                    <span>{copiedCaption ? "Đã chép" : "Sao chép"}</span>
                  </button>
                </div>
                <div className="p-3 rounded-lg border border-border bg-muted/30 text-foreground font-sans whitespace-pre-wrap max-h-36 overflow-y-auto leading-relaxed select-text">
                  {packageData?.caption || post.caption || "(Chưa có caption)"}
                </div>
              </div>

              {/* Hashtags Section */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                    Hashtags
                  </span>
                  <button
                    type="button"
                    onClick={handleCopyTags}
                    className="flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-muted text-primary text-[11px] transition-colors"
                  >
                    {copiedTags ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                    <span>{copiedTags ? "Đã chép" : "Sao chép"}</span>
                  </button>
                </div>
                <div className="p-2.5 rounded-lg border border-border bg-muted/30 text-primary font-mono text-[11px] select-text">
                  {packageData?.hashtags || (post.hashtags ? post.hashtags.join(" ") : "(Không có hashtags)")}
                </div>
              </div>

              {/* Checklist */}
              {packageData?.checklist && (
                <div className="space-y-1.5 pt-1">
                  <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                    Hướng dẫn đăng bài
                  </span>
                  <div className="p-3 rounded-lg border border-border/60 bg-muted/20 text-[11px] text-muted-foreground whitespace-pre-wrap font-sans leading-relaxed select-text">
                    {packageData.checklist}
                  </div>
                </div>
              )}

              {/* Mark Published Panel */}
              <div className="p-3.5 rounded-xl border border-border bg-card space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-semibold text-foreground">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span>Xác nhận hoàn thành đăng bài</span>
                  </div>
                  {!showMarkInput && (
                    <button
                      type="button"
                      onClick={() => setShowMarkInput(true)}
                      className="px-2.5 py-1 rounded-md bg-emerald-600 text-white font-medium text-[11px] hover:bg-emerald-500 transition-colors"
                    >
                      Tôi đã đăng xong
                    </button>
                  )}
                </div>

                {showMarkInput && (
                  <div className="space-y-2 pt-1 animate-in fade-in">
                    <p className="text-[11px] text-muted-foreground">
                      Dán đường dẫn (URL) bài viết thật sau khi đã đăng trên {post.platform.toUpperCase()}:
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="url"
                        placeholder={`https://www.${post.platform}.com/...`}
                        value={postedUrl}
                        onChange={(e) => setPostedUrl(e.target.value)}
                        className="flex-1 px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                      <button
                        type="button"
                        disabled={marking}
                        onClick={handleMarkPublishedConfirm}
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-500 transition-colors shrink-0 disabled:opacity-50"
                      >
                        {marking ? "Đang lưu..." : "Xác nhận"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
