"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { SocialAccount, PlatformType, PostingWindow, socialApi } from "@/lib/api/social";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  Plus,
  RefreshCw,
  Settings,
  Tag,
  Trash2,
  X,
} from "./icons";

interface AccountDetailSheetProps {
  projectId: string;
  isOpen: boolean;
  account: SocialAccount | null; // null means create new
  isNew?: boolean;
  totalAccountsCount: number;
  onClose: () => void;
  onSaved: () => void;
}

const WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"];

export function AccountDetailSheet({
  projectId,
  isOpen,
  account,
  isNew = false,
  totalAccountsCount,
  onClose,
  onSaved,
}: AccountDetailSheetProps) {
  const [platform, setPlatform] = useState<PlatformType>(account?.platform || "tiktok");
  const [handle, setHandle] = useState<string>(account?.handle || "");
  const [displayName, setDisplayName] = useState<string>(account?.display_name || "");
  const [avatar, setAvatar] = useState<string>(account?.avatar || "");
  const [groups, setGroups] = useState<string>((account?.groups || []).join(", "));
  const [dailyLimit, setDailyLimit] = useState<number>(account?.daily_limit || 5);
  const [minGapMinutes, setMinGapMinutes] = useState<number>(account?.min_gap_minutes || 120);
  const [hashtags, setHashtags] = useState<string>((account?.default_hashtags || []).join(" "));
  const [captionFooter, setCaptionFooter] = useState<string>(account?.default_caption_footer || "");
  const [authMode, setAuthMode] = useState<"manual" | "oauth">(account?.auth?.mode === "oauth" ? "oauth" : "manual");
  const [postingWindows, setPostingWindows] = useState<PostingWindow[]>(
    account?.posting_windows?.length
      ? account.posting_windows
      : [
          { weekday: 0, start: "19:00", end: "21:00" },
          { weekday: 2, start: "19:00", end: "21:00" },
          { weekday: 4, start: "19:00", end: "21:00" },
        ]
  );
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim() || !displayName.trim()) {
      alert("Vui lòng điền Handle và Tên hiển thị");
      return;
    }

    if (isNew && totalAccountsCount >= 10) {
      alert("Đã đạt giới hạn tối đa 10 tài khoản");
      return;
    }

    setIsSaving(true);
    try {
      const parsedHashtags = hashtags
        .split(/[\s,]+/)
        .map((t) => (t.startsWith("#") ? t : `#${t}`))
        .filter((t) => t.length > 1);

      const parsedGroups = groups
        .split(",")
        .map((g) => g.trim())
        .filter(Boolean);

      const payload: Partial<SocialAccount> = {
        platform,
        handle: handle.trim(),
        display_name: displayName.trim(),
        avatar: avatar.trim(),
        groups: parsedGroups,
        daily_limit: dailyLimit,
        min_gap_minutes: minGapMinutes,
        default_hashtags: parsedHashtags,
        default_caption_footer: captionFooter.trim(),
        posting_windows: postingWindows,
        auth: { mode: authMode },
        status: authMode === "oauth" ? (account?.status || "manual") : "manual",
      };

      if (isNew) {
        await socialApi.createAccount(projectId, payload);
      } else if (account) {
        await socialApi.updateAccount(projectId, account.id, payload);
      }

      onSaved();
      onClose();
    } catch (err: any) {
      alert(`Lỗi lưu tài khoản: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!account) return;
    if (confirm(`Bạn có chắc chắn muốn xóa tài khoản ${account.display_name}?`)) {
      try {
        await socialApi.deleteAccount(projectId, account.id);
        onSaved();
        onClose();
      } catch (err: any) {
        alert(`Lỗi xóa tài khoản: ${err.message}`);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/50 backdrop-blur-xs animate-in fade-in-50">
      <div className="relative h-full w-full max-w-md bg-card border-l border-border shadow-2xl flex flex-col overflow-hidden text-foreground">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border bg-muted/30 px-4 py-3 shrink-0">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Settings className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-foreground">
                {isNew ? "Thêm tài khoản mạng xã hội" : `Cấu hình: ${displayName || handle}`}
              </h3>
              <p className="text-[10px] text-muted-foreground">
                {isNew ? `Tài khoản ${totalAccountsCount + 1}/10` : "Quản lý khung giờ vàng & thông số"}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {/* Platform selection */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-muted-foreground">Nền tảng:</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as PlatformType)}
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground font-medium"
            >
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="threads">Threads</option>
              <option value="x">X (Twitter)</option>
            </select>
          </div>

          {/* Handle and Display Name */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground">Handle / ID:</label>
              <input
                type="text"
                required
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                placeholder="@kenh.official"
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground font-mono placeholder:text-muted-foreground"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground">Tên hiển thị:</label>
              <input
                type="text"
                required
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Sóc Nhỏ TV"
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground"
              />
            </div>
          </div>

          {/* Groups tag */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-muted-foreground">
              Nhóm phân loại (ngăn cách bằng dấu phẩy):
            </label>
            <input
              type="text"
              value={groups}
              onChange={(e) => setGroups(e.target.value)}
              placeholder="Kênh chính, Bán hàng, Hoạt hình"
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground"
            />
          </div>

          {/* Auth mode & status */}
          <div className="rounded-xl border border-border bg-muted/20 p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-foreground">Chế độ xuất bản:</span>
              <div className="flex items-center rounded-lg border border-border bg-background p-0.5 text-[11px]">
                <button
                  type="button"
                  onClick={() => setAuthMode("manual")}
                  className={cn(
                    "rounded-md px-2 py-0.5 font-medium transition-all",
                    authMode === "manual" ? "bg-primary text-primary-foreground" : "text-muted-foreground"
                  )}
                >
                  Thủ công (Gói ZIP)
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode("oauth")}
                  className={cn(
                    "rounded-md px-2 py-0.5 font-medium transition-all",
                    authMode === "oauth" ? "bg-primary text-primary-foreground" : "text-muted-foreground"
                  )}
                >
                  OAuth API
                </button>
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              {authMode === "manual"
                ? "Tự động sinh trọn bộ tệp tiêu đề, video, cover và nút 'Tôi đã đăng' để tiện thao tác."
                : "Kết nối trực tiếp qua OAuth API chính thức, lưu token an toàn trong key vault."}
            </p>
          </div>

          {/* Daily limit & min gap */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground">Giới hạn bài/ngày:</label>
              <input
                type="number"
                min={1}
                max={50}
                value={dailyLimit}
                onChange={(e) => setDailyLimit(parseInt(e.target.value) || 1)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground font-mono"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground">Khoảng cách tối thiểu (phút):</label>
              <input
                type="number"
                min={15}
                max={1440}
                value={minGapMinutes}
                onChange={(e) => setMinGapMinutes(parseInt(e.target.value) || 60)}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground font-mono"
              />
            </div>
          </div>

          {/* Posting Windows (Golden hours) */}
          <div className="space-y-2 rounded-xl border border-border bg-muted/10 p-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-foreground flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-primary" />
                Khung giờ vàng xuất bản (7 ngày):
              </span>
              <button
                type="button"
                onClick={() => {
                  setPostingWindows([
                    ...postingWindows,
                    { weekday: 0, start: "19:00", end: "21:00" },
                  ]);
                }}
                className="text-[10px] font-bold text-primary hover:underline flex items-center gap-0.5"
              >
                <Plus className="h-3 w-3" />
                Thêm khung giờ
              </button>
            </div>

            <div className="space-y-1.5">
              {postingWindows.map((pw, idx) => (
                <div key={`${pw.weekday}-${pw.start}-${pw.end}-${idx}`} className="flex items-center gap-2 rounded-lg border border-border bg-background p-1.5 text-xs">
                  <select
                    value={pw.weekday}
                    onChange={(e) => {
                      const newW = parseInt(e.target.value);
                      setPostingWindows(
                        postingWindows.map((item, i) => (i === idx ? { ...item, weekday: newW } : item))
                      );
                    }}
                    className="rounded-md border border-border bg-muted/50 px-2 py-1 text-xs text-foreground"
                  >
                    {WEEKDAYS.map((wd, dayIdx) => (
                      <option key={dayIdx} value={dayIdx}>
                        {wd}
                      </option>
                    ))}
                  </select>

                  <input
                    type="time"
                    value={pw.start}
                    onChange={(e) => {
                      const val = e.target.value;
                      setPostingWindows(
                        postingWindows.map((item, i) => (i === idx ? { ...item, start: val } : item))
                      );
                    }}
                    className="rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground font-mono"
                  />
                  <span className="text-muted-foreground">-</span>
                  <input
                    type="time"
                    value={pw.end}
                    onChange={(e) => {
                      const val = e.target.value;
                      setPostingWindows(
                        postingWindows.map((item, i) => (i === idx ? { ...item, end: val } : item))
                      );
                    }}
                    className="rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground font-mono"
                  />

                  <button
                    type="button"
                    onClick={() => {
                      setPostingWindows(postingWindows.filter((_, i) => i !== idx));
                    }}
                    className="text-muted-foreground hover:text-rose-500 p-1"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Default hashtags & footer */}
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-muted-foreground">Hashtags mặc định:</label>
            <input
              type="text"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              placeholder="#socnhotv #hoathinh3d"
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-muted-foreground">Chữ ký chân bài (Footer):</label>
            <textarea
              rows={2}
              value={captionFooter}
              onChange={(e) => setCaptionFooter(e.target.value)}
              placeholder="Đăng ký kênh để theo dõi tập mới nhé!"
              className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground"
            />
          </div>

          {/* Bottom Actions */}
          <div className="flex items-center justify-between gap-3 pt-3 border-t border-border">
            {!isNew && (
              <button
                type="button"
                onClick={handleDelete}
                className="flex items-center gap-1 text-xs font-semibold text-rose-500 hover:bg-rose-500/10 px-3 py-2 rounded-xl transition-colors"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Xóa kênh</span>
              </button>
            )}

            <div className="flex items-center gap-2 ml-auto">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-border px-3.5 py-2 text-xs font-semibold text-foreground hover:bg-accent transition-colors shadow-2xs"
              >
                Đóng
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-primary-foreground hover:bg-primary/90 transition-colors shadow disabled:opacity-50"
              >
                <Check className="h-4 w-4" />
                <span>{isSaving ? "Đang lưu..." : isNew ? "Tạo tài khoản" : "Lưu thay đổi"}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
