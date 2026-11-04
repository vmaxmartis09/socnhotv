"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { PlatformType, PostingWindow, SocialAccount, socialApi } from "@/lib/api/social";
import {
  CalendarDays,
  CheckCircle2,
  Link2,
  Plus,
  Settings,
  Trash2,
  X,
  AlertTriangle,
} from "@/components/ui/icons";
import { Clock } from "./icons";

interface AccountsTabProps {
  projectId: string;
}

const PLATFORMS: { id: PlatformType; name: string; color: string }[] = [
  { id: "youtube", name: "YouTube", color: "text-red-500 bg-red-500/10 border-red-500/20" },
  { id: "tiktok", name: "TikTok", color: "text-cyan-500 bg-cyan-500/10 border-cyan-500/20" },
  { id: "facebook", name: "Facebook", color: "text-blue-500 bg-blue-500/10 border-blue-500/20" },
  { id: "instagram", name: "Instagram", color: "text-pink-500 bg-pink-500/10 border-pink-500/20" },
  { id: "douyin", name: "Douyin", color: "text-amber-500 bg-amber-500/10 border-amber-500/20" },
  { id: "threads", name: "Threads", color: "text-zinc-500 bg-zinc-500/10 border-zinc-500/20" },
  { id: "x", name: "X (Twitter)", color: "text-neutral-500 bg-neutral-500/10 border-neutral-500/20" },
];

const WEEKDAY_NAMES = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export function AccountsTab({ projectId }: AccountsTabProps) {
  const { accounts, loadAccounts, posts } = useSocialStore();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingWindowsAccount, setEditingWindowsAccount] = useState<SocialAccount | null>(null);

  // Form states for adding account
  const [platform, setPlatform] = useState<PlatformType>("youtube");
  const [authMode, setAuthMode] = useState<"manual" | "oauth">("manual");
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [channelUrl, setChannelUrl] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [footer, setFooter] = useState("");

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim() || !displayName.trim()) {
      alert("Vui lòng điền handle và tên hiển thị");
      return;
    }

    try {
      await socialApi.createAccount(projectId, {
        platform,
        handle: handle.trim(),
        display_name: displayName.trim(),
        channel_url: channelUrl.trim(),
        auth: { mode: authMode },
        status: authMode === "oauth" ? "manual" : "connected",
        default_hashtags: hashtags
          .split(/[\s,]+/)
          .filter(Boolean)
          .map((h) => (h.startsWith("#") ? h : `#${h}`)),
        default_caption_footer: footer.trim(),
        posting_windows: [
          { weekday: 0, start: "19:00", end: "21:00" },
          { weekday: 2, start: "19:00", end: "21:00" },
          { weekday: 4, start: "19:00", end: "21:00" },
        ],
        daily_limit: 5,
      });

      setIsAddOpen(false);
      setHandle("");
      setDisplayName("");
      setChannelUrl("");
      setHashtags("");
      setFooter("");
      await loadAccounts(projectId);
    } catch (err: any) {
      alert(`Lỗi tạo tài khoản: ${err.message}`);
    }
  };

  const handleDeleteAccount = async (accId: string) => {
    if (!window.confirm("Bạn có chắc muốn xoá tài khoản này?")) return;
    try {
      await socialApi.deleteAccount(projectId, accId);
      await loadAccounts(projectId);
    } catch (err: any) {
      alert(`Lỗi xoá tài khoản: ${err.message}`);
    }
  };

  const handleSaveWindows = async (windows: PostingWindow[]) => {
    if (!editingWindowsAccount) return;
    try {
      await socialApi.updateAccount(projectId, editingWindowsAccount.id, {
        ...editingWindowsAccount,
        posting_windows: windows,
      });
      setEditingWindowsAccount(null);
      await loadAccounts(projectId);
    } catch (err: any) {
      alert(`Lỗi lưu khung giờ: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Tài khoản mạng xã hội ({accounts.length})
          </h2>
          <p className="text-xs text-muted-foreground">
            Quản lý tài khoản đăng bài, token OAuth và cấu hình khung giờ vàng cho từng kênh.
          </p>
        </div>
      </div>

      {/* Grid of Account Cards + Dashed Add Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc) => {
          const platInfo = PLATFORMS.find((p) => p.id === acc.platform) || PLATFORMS[0];
          // Count scheduled posts for this account
          const scheduledCount = posts.reduce((accCount, p) => {
            const hasTarget = p.targets.some(
              (t) => t.account_id === acc.id && (t.status === "scheduled" || t.status === "pending_approval")
            );
            return hasTarget ? accCount + 1 : accCount;
          }, 0);

          return (
            <div
              key={acc.id}
              className="flex flex-col justify-between rounded-xl border border-border bg-card p-4 shadow-2xs transition-all hover:border-border/80"
            >
              <div className="space-y-3">
                {/* Header: Platform & Status */}
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                      platInfo.color
                    )}
                  >
                    {platInfo.name}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs">
                    {acc.status === "connected" && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="h-3 w-3" /> Đã kết nối
                      </span>
                    )}
                    {acc.status === "manual" && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
                        <Link2 className="h-3 w-3" /> Thủ công
                      </span>
                    )}
                    {acc.status === "expired" && (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-amber-500">
                        <AlertTriangle className="h-3 w-3" /> Hết hạn
                      </span>
                    )}
                  </div>
                </div>

                {/* Account Info */}
                <div className="flex items-center gap-3 pt-1">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm border border-primary/20">
                    {acc.display_name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-sm truncate text-foreground">
                      {acc.display_name}
                    </h3>
                    <p className="text-xs text-muted-foreground truncate">{acc.handle}</p>
                  </div>
                </div>

                {/* Metrics & Posting Windows */}
                <div className="rounded-lg border border-border bg-muted/30 p-2.5 text-xs space-y-1.5">
                  <div className="flex justify-between text-muted-foreground text-[11px]">
                    <span>Bài chờ / lên lịch:</span>
                    <span className="font-semibold text-foreground">{scheduledCount} bài</span>
                  </div>
                  <div className="flex justify-between text-muted-foreground text-[11px]">
                    <span>Giới hạn ngày:</span>
                    <span className="font-semibold text-foreground">{acc.daily_limit} bài/ngày</span>
                  </div>
                  <div className="pt-1 border-t border-border/50">
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-medium text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" /> Khung giờ vàng
                      </span>
                      <button
                        onClick={() => setEditingWindowsAccount(acc)}
                        className="text-primary hover:underline font-medium text-[10px]"
                      >
                        Chỉnh sửa
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {acc.posting_windows.length === 0 ? (
                        <span className="text-[10px] text-muted-foreground italic">Chưa cài đặt</span>
                      ) : (
                        acc.posting_windows.slice(0, 4).map((w, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-background border border-border px-1.5 py-0.2 text-[10px] font-mono"
                          >
                            {WEEKDAY_NAMES[w.weekday]}: {w.start}
                          </span>
                        ))
                      )}
                      {acc.posting_windows.length > 4 && (
                        <span className="text-[10px] text-muted-foreground">
                          +{acc.posting_windows.length - 4}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions Footer */}
              <div className="flex items-center justify-between pt-3 mt-2 border-t border-border">
                <button
                  onClick={() => alert("Kết nối OAuth chính chủ sẽ được mở và xử lý ở giai đoạn C3.")}
                  className="rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted text-foreground flex items-center gap-1"
                >
                  <Link2 className="h-3 w-3" />
                  <span>{acc.status === "connected" ? "Làm mới Token" : "Kết nối OAuth"}</span>
                </button>
                <button
                  onClick={() => handleDeleteAccount(acc.id)}
                  title="Xoá tài khoản"
                  className="rounded p-1 text-muted-foreground hover:bg-rose-500/10 hover:text-rose-500 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}

        {/* Dashed Add Card next to last card */}
        <button
          onClick={() => setIsAddOpen(true)}
          className="flex min-h-[220px] flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border bg-muted/10 p-6 text-center transition-colors hover:border-primary/50 hover:bg-primary/5 cursor-pointer group"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background group-hover:border-primary/40 group-hover:scale-105 transition-all">
            <Plus className="h-5 w-5 text-muted-foreground group-hover:text-primary" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Thêm tài khoản mới</h4>
            <p className="text-xs text-muted-foreground mt-0.5">
              Kết nối kênh YouTube, TikTok, Facebook, Instagram...
            </p>
          </div>
        </button>
      </div>

      {/* Add Account Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <form
            onSubmit={handleCreateAccount}
            className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-xl space-y-4"
          >
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-semibold text-foreground">Thêm tài khoản mạng xã hội</h3>
              <button
                type="button"
                onClick={() => setIsAddOpen(false)}
                className="rounded p-1 hover:bg-muted text-muted-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-muted-foreground block mb-1">Nền tảng</label>
                <div className="grid grid-cols-4 gap-1.5">
                  {PLATFORMS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setPlatform(p.id)}
                      className={cn(
                        "rounded-md border p-1.5 font-semibold text-center uppercase tracking-wider transition-all",
                        platform === p.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-background text-muted-foreground hover:bg-muted"
                      )}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">Chế độ kết nối</label>
                <div className="flex gap-2">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="authMode"
                      value="manual"
                      checked={authMode === "manual"}
                      onChange={() => setAuthMode("manual")}
                    />
                    <span>Thủ công (Manual / Export Package)</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="authMode"
                      value="oauth"
                      checked={authMode === "oauth"}
                      onChange={() => setAuthMode("oauth")}
                    />
                    <span>OAuth chính chủ</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">Tên kênh / Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Sóc Nhỏ TV Official"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background p-2 focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">Handle / Username</label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: @socnhotv"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background p-2 focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">URL Kênh (tuỳ chọn)</label>
                <input
                  type="url"
                  placeholder="https://youtube.com/@socnhotv"
                  value={channelUrl}
                  onChange={(e) => setChannelUrl(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background p-2 focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">Hashtag mặc định</label>
                <input
                  type="text"
                  placeholder="#socnhotv #hoathinh3d"
                  value={hashtags}
                  onChange={(e) => setHashtags(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background p-2 focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>

              <div>
                <label className="font-medium text-muted-foreground block mb-1">Chữ ký chân bài (Footer)</label>
                <textarea
                  placeholder="Theo dõi kênh để đón xem tập mới vào 19h mỗi ngày nhé!"
                  value={footer}
                  onChange={(e) => setFooter(e.target.value)}
                  className="w-full h-16 rounded-lg border border-border bg-background p-2 focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                type="button"
                onClick={() => setIsAddOpen(false)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                Huỷ
              </button>
              <button
                type="submit"
                className="rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90"
              >
                Tạo tài khoản
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Posting Windows Modal Editor */}
      {editingWindowsAccount && (
        <PostingWindowsModal
          account={editingWindowsAccount}
          onClose={() => setEditingWindowsAccount(null)}
          onSave={handleSaveWindows}
        />
      )}
    </div>
  );
}

function PostingWindowsModal({
  account,
  onClose,
  onSave,
}: {
  account: SocialAccount;
  onClose: () => void;
  onSave: (windows: PostingWindow[]) => void;
}) {
  const [windows, setWindows] = useState<PostingWindow[]>(account.posting_windows || []);
  const [newWeekday, setNewWeekday] = useState(0);
  const [newStart, setNewStart] = useState("19:00");
  const [newEnd, setNewEnd] = useState("21:00");

  const addWindow = () => {
    setWindows([...windows, { weekday: newWeekday, start: newStart, end: newEnd }]);
  };

  const removeWindow = (idx: number) => {
    setWindows(windows.filter((_, i) => i !== idx));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h3 className="text-base font-semibold text-foreground">
            Khung giờ vàng: {account.display_name}
          </h3>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3 text-xs">
          <p className="text-muted-foreground">
            Lịch đăng tự động sẽ ưu tiên xếp bài vào các khung giờ vàng này:
          </p>

          <div className="max-h-48 overflow-y-auto space-y-1.5 divide-y divide-border/40">
            {windows.length === 0 ? (
              <p className="text-center text-muted-foreground py-4 italic">Chưa có khung giờ nào</p>
            ) : (
              windows.map((w, idx) => (
                <div key={idx} className="flex items-center justify-between pt-1">
                  <span className="font-semibold text-foreground">
                    {WEEKDAY_NAMES[w.weekday]} ({w.start} - {w.end})
                  </span>
                  <button
                    onClick={() => removeWindow(idx)}
                    className="text-rose-500 hover:text-rose-600 p-1"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-border">
            <select
              value={newWeekday}
              onChange={(e) => setNewWeekday(parseInt(e.target.value, 10))}
              className="rounded border border-border bg-background p-1 text-xs"
            >
              {WEEKDAY_NAMES.map((name, i) => (
                <option key={i} value={i}>
                  Thứ {i + 2 === 8 ? "CN" : i + 2}
                </option>
              ))}
            </select>
            <input
              type="time"
              value={newStart}
              onChange={(e) => setNewStart(e.target.value)}
              className="rounded border border-border bg-background p-1 text-xs"
            />
            <span>đến</span>
            <input
              type="time"
              value={newEnd}
              onChange={(e) => setNewEnd(e.target.value)}
              className="rounded border border-border bg-background p-1 text-xs"
            />
            <button
              onClick={addWindow}
              className="rounded bg-muted px-2 py-1 font-semibold hover:bg-muted/80"
            >
              Thêm
            </button>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-border">
          <button onClick={onClose} className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted">
            Huỷ
          </button>
          <button
            onClick={() => onSave(windows)}
            className="rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90"
          >
            Lưu thay đổi
          </button>
        </div>
      </div>
    </div>
  );
}
