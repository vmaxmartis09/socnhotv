"use client";

import React, { useEffect, useState } from "react";
import { useStudioStore } from "@/store";
import { useSocialStore } from "@/store/modules/social";
import { socialApi, type SocialAccount, type PlatformType } from "@/lib/api/social";
import { AgendaList } from "@/components/social/AgendaList";
import { PostComposer } from "@/components/social/PostComposer";
import { CalendarView } from "@/components/social/CalendarView";
import { Clock } from "@/components/social/icons";
import {
  CalendarDays,
  Plus,
  Settings,
  ShieldCheck,
  CheckCircle2,
  X,
  ExternalLink,
  Loader2,
  AlertTriangle,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

export function PublishTab() {
  const { activeProjectId } = useStudioStore();
  const {
    calendarData,
    accounts,
    posts,
    loadAll,
    openComposer,
  } = useSocialStore();

  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const [isAddAccountOpen, setIsAddAccountOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<SocialAccount | null>(null);

  // New account form
  const [newPlatform, setNewPlatform] = useState<PlatformType>("tiktok");
  const [newHandle, setNewHandle] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newAuthMode, setNewAuthMode] = useState<"manual" | "oauth">("manual");
  const [isSavingAccount, setIsSavingAccount] = useState(false);

  useEffect(() => {
    if (activeProjectId) {
      loadAll(activeProjectId);
    }
  }, [activeProjectId, loadAll]);

  const items = calendarData?.items || [];

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHandle.trim() || !newDisplayName.trim()) return;
    setIsSavingAccount(true);
    try {
      await socialApi.createAccount(activeProjectId, {
        platform: newPlatform,
        handle: newHandle.trim(),
        display_name: newDisplayName.trim(),
        auth: { mode: newAuthMode },
        status: newAuthMode === "oauth" ? "manual" : "connected",
        default_hashtags: ["#socnhotv", `#${newPlatform}`],
        posting_windows: [
          { weekday: 0, start: "19:00", end: "21:00" },
          { weekday: 2, start: "19:00", end: "21:00" },
          { weekday: 4, start: "19:00", end: "21:00" },
        ],
        daily_limit: 5,
      });
      setIsAddAccountOpen(false);
      setNewHandle("");
      setNewDisplayName("");
      await loadAll(activeProjectId);
    } catch (err: any) {
      alert(`Lỗi tạo tài khoản: ${err.message}`);
    } finally {
      setIsSavingAccount(false);
    }
  };

  const handleQuickApprove = async (postId: string) => {
    try {
      await socialApi.approvePost(activeProjectId, postId);
      await loadAll(activeProjectId);
    } catch (err: any) {
      alert(`Lỗi duyệt bài: ${err.message}`);
    }
  };

  const handleMarkPublished = async (postId: string, targetId: string) => {
    const url = window.prompt("Nhập URL bài viết đã đăng trên mạng xã hội:");
    if (!url) return;
    try {
      await socialApi.markPublished(activeProjectId, postId, targetId, url);
      await loadAll(activeProjectId);
    } catch (err: any) {
      alert(`Lỗi cập nhật: ${err.message}`);
    }
  };

  return (
    <div className="p-3.5 space-y-4 text-xs select-none">
      {/* Top Banner & Calendar Trigger */}
      <div className="flex items-center justify-between rounded-xl border border-border bg-card p-3 shadow-2xs">
        <div className="space-y-0.5">
          <h4 className="font-semibold text-foreground text-xs flex items-center gap-1.5">
            <CalendarDays className="h-4 w-4 text-primary" />
            Quản lý Xuất bản & Đăng bài
          </h4>
          <p className="text-[11px] text-muted-foreground">
            {accounts.length} kênh kết nối · {items.length} bài đã lên lịch
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCalendarModalOpen(true)}
          className="flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-accent transition-colors shadow-2xs"
        >
          <CalendarDays className="h-3.5 w-3.5 text-primary" />
          <span>Xem Lịch</span>
        </button>
      </div>

      {/* Accounts Section */}
      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-muted-foreground">
            Tài khoản mạng xã hội ({accounts.length})
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {accounts.map((acc) => {
            const isConnected = acc.status === "connected";
            const windowText = acc.posting_windows?.[0]
              ? `${acc.posting_windows[0].start} - ${acc.posting_windows[0].end}`
              : "19:00 - 21:00";

            return (
              <div
                key={acc.id}
                onClick={() => setEditingAccount(acc)}
                className="group flex flex-col justify-between rounded-xl border border-border bg-card p-2.5 cursor-pointer hover:border-primary/50 transition-all shadow-2xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent font-bold uppercase text-[11px] text-foreground">
                      {acc.platform.slice(0, 2)}
                    </div>
                    <div>
                      <p className="font-semibold text-foreground line-clamp-1">
                        {acc.display_name || acc.handle}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {acc.handle}
                      </p>
                    </div>
                  </div>
                  <span
                    className={cn(
                      "rounded-full px-1.5 py-0.2 text-[9px] font-semibold uppercase",
                      isConnected
                        ? "bg-emerald-500/10 text-emerald-500"
                        : "bg-amber-500/10 text-amber-500"
                    )}
                  >
                    {acc.auth?.mode === "oauth" ? "OAuth" : "Thủ công"}
                  </span>
                </div>

                <div className="mt-2 flex items-center justify-between border-t border-border/50 pt-1.5 text-[10px] text-muted-foreground">
                  <span className="flex items-center gap-1 font-mono">
                    <Clock className="h-3 w-3" />
                    {windowText}
                  </span>
                  <span className="text-primary group-hover:underline">
                    Sửa khung giờ
                  </span>
                </div>
              </div>
            );
          })}

          {/* Add Account Dashed Card */}
          <button
            type="button"
            onClick={() => setIsAddAccountOpen(true)}
            className="flex min-h-[72px] flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-border p-2.5 text-muted-foreground hover:border-primary/50 hover:bg-primary/5 hover:text-foreground transition-all"
          >
            <Plus className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold">+ Thêm tài khoản</span>
          </button>
        </div>
      </section>

      {/* Action: Add Schedule Button */}
      <button
        type="button"
        onClick={() => openComposer()}
        className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow"
      >
        <Plus className="h-4 w-4" />
        <span>+ Lên lịch xuất bản video</span>
      </button>

      {/* Upcoming Agenda List */}
      <section className="space-y-2 border-t border-border pt-3">
        <div className="flex items-center justify-between">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-muted-foreground">
            Lịch đăng sắp tới (7 ngày)
          </span>
          <span className="font-mono text-[11px] text-muted-foreground">
            {items.length} bài
          </span>
        </div>

        <AgendaList
          items={items}
          maxDays={7}
          onItemClick={(item) => {
            const p = posts.find((x) => x.id === item.post_id);
            if (p) openComposer(p);
          }}
          emptyMessage="Chưa có bài viết nào được lên lịch trong 7 ngày tới."
        />

        {/* Draft Pending Approval Items */}
        {posts.some((p) => p.status === "draft") && (
          <div className="mt-3 space-y-1.5 rounded-xl border border-amber-500/30 bg-amber-500/5 p-3">
            <span className="text-[11px] font-semibold text-amber-500 flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5" />
              Bài chờ duyệt trước khi đăng:
            </span>
            <div className="space-y-1">
              {posts
                .filter((p) => p.status === "draft")
                .map((draft) => (
                  <div
                    key={draft.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-card p-2 text-xs"
                  >
                    <span className="truncate max-w-[200px] font-medium text-foreground">
                      {draft.title}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => openComposer(draft)}
                        className="rounded px-2 py-0.5 text-[11px] text-muted-foreground hover:bg-accent"
                      >
                        Sửa
                      </button>
                      <button
                        type="button"
                        onClick={() => handleQuickApprove(draft.id)}
                        className="rounded bg-primary px-2 py-0.5 text-[11px] font-semibold text-primary-foreground hover:bg-primary/90"
                      >
                        Duyệt ngay
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </section>

      {/* Post Composer Drawer instance */}
      <PostComposer projectId={activeProjectId} />

      {/* Large Calendar View Modal */}
      {isCalendarModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-background/80 backdrop-blur-sm">
          <div className="relative flex flex-col w-full max-w-5xl h-[88vh] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-accent/30 shrink-0">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <CalendarDays className="h-4 w-4 text-primary" />
                Lịch xuất bản mạng xã hội (Kéo thả đổi giờ)
              </h3>
              <button
                onClick={() => setIsCalendarModalOpen(false)}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 scroll-quiet">
              <CalendarView projectId={activeProjectId} />
            </div>
          </div>
        </div>
      )}

      {/* Add Account Modal */}
      {isAddAccountOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <form
            onSubmit={handleCreateAccount}
            className="w-full max-w-md rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-border pb-2.5">
              <h3 className="text-sm font-semibold text-foreground">Thêm tài khoản mạng xã hội</h3>
              <button
                type="button"
                onClick={() => setIsAddAccountOpen(false)}
                className="rounded p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Nền tảng:</label>
                <select
                  value={newPlatform}
                  onChange={(e) => setNewPlatform(e.target.value as PlatformType)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
                >
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                  <option value="facebook">Facebook</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Tên hiển thị:</label>
                <input
                  type="text"
                  placeholder="Vd: Sóc Nhỏ TV Official"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Handle / @Username:</label>
                <input
                  type="text"
                  placeholder="Vd: @socnhotv.official"
                  value={newHandle}
                  onChange={(e) => setNewHandle(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Phương thức kết nối:</label>
                <select
                  value={newAuthMode}
                  onChange={(e) => setNewAuthMode(e.target.value as any)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
                >
                  <option value="manual">Thủ công (Nhắc và tạo gói đăng tay)</option>
                  <option value="oauth">OAuth chính chủ (Tự động đăng khi duyệt)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={() => setIsAddAccountOpen(false)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={isSavingAccount}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                {isSavingAccount && <Loader2 className="h-3 w-3 animate-spin" />}
                <span>Lưu tài khoản</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Posting Windows Modal */}
      {editingAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-border pb-2.5">
              <h3 className="text-sm font-semibold text-foreground">
                Khung giờ đăng ({editingAccount.display_name})
              </h3>
              <button
                type="button"
                onClick={() => setEditingAccount(null)}
                className="rounded p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-muted-foreground">
                Khung giờ gợi ý hàng ngày cho kênh này:
              </p>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">Giờ bắt đầu:</label>
                  <input
                    type="time"
                    defaultValue={editingAccount.posting_windows?.[0]?.start || "19:00"}
                    id="win_start"
                    className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">Giờ kết thúc:</label>
                  <input
                    type="time"
                    defaultValue={editingAccount.posting_windows?.[0]?.end || "21:00"}
                    id="win_end"
                    className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={() => setEditingAccount(null)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-foreground hover:bg-accent"
              >
                Đóng
              </button>
              <button
                type="button"
                onClick={async () => {
                  const start = (document.getElementById("win_start") as HTMLInputElement)?.value || "19:00";
                  const end = (document.getElementById("win_end") as HTMLInputElement)?.value || "21:00";
                  await socialApi.updateAccount(activeProjectId, editingAccount.id, {
                    posting_windows: [
                      { weekday: 0, start, end },
                      { weekday: 1, start, end },
                      { weekday: 2, start, end },
                      { weekday: 3, start, end },
                      { weekday: 4, start, end },
                      { weekday: 5, start, end },
                      { weekday: 6, start, end },
                    ],
                  });
                  await loadAll(activeProjectId);
                  setEditingAccount(null);
                }}
                className="rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Lưu khung giờ
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
