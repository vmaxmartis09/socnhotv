"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { useStudioStore } from "@/store";
import {
  Plus,
  RefreshCw,
  Trash2,
  ExternalLink,
  Flame,
  Clock,
  AlertCircle,
  CheckCircle,
  X,
} from "@/components/ui/icons";
import { SocialAccount, PlatformType } from "@/lib/api/social";

interface AccountsViewProps {
  onRefresh?: () => void;
}

export function AccountsView({ onRefresh }: AccountsViewProps) {
  const { activeProjectId } = useStudioStore();
  const {
    accounts,
    loadAccounts,
    accountsStats,
    loadAccountsStats,
    setHubSelectedEntity,
  } = useSocialStore();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<SocialAccount | null>(null);
  const [formPlatform, setFormPlatform] = useState<PlatformType>("youtube");
  const [formDisplayName, setFormDisplayName] = useState("");
  const [formHandle, setFormHandle] = useState("");
  const [formGroup, setFormGroup] = useState("official");
  const [formAuthMode, setFormAuthMode] = useState<"oauth" | "manual">("manual");
  const [formDailyLimit, setFormDailyLimit] = useState(3);
  const [formGoldenWindows, setFormGoldenWindows] = useState<string[]>(["11:30", "19:30"]);
  const [errorMessage, setErrorMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (activeProjectId) {
      loadAccounts(activeProjectId);
      loadAccountsStats(activeProjectId);
    }
  }, [activeProjectId, loadAccounts, loadAccountsStats]);

  const maxAccounts = 10;
  const currentCount = accounts.length;
  const isFull = currentCount >= maxAccounts;

  const handleOpenAdd = () => {
    setEditingAccount(null);
    setFormPlatform("youtube");
    setFormDisplayName("");
    setFormHandle("");
    setFormGroup("official");
    setFormAuthMode("manual");
    setFormDailyLimit(3);
    setFormGoldenWindows(["11:30", "19:30"]);
    setErrorMessage("");
    setIsAddModalOpen(true);
  };

  const handleOpenEdit = (acc: SocialAccount) => {
    setEditingAccount(acc);
    setFormPlatform(acc.platform);
    setFormDisplayName(acc.display_name);
    setFormHandle(acc.handle);
    setFormGroup(acc.group || acc.groups?.[0] || "official");
    setFormAuthMode((acc.auth_mode === "oauth" || acc.auth?.mode === "oauth") ? "oauth" : "manual");
    setFormDailyLimit(acc.limits?.daily || acc.daily_limit || 3);
    setFormGoldenWindows(acc.golden_windows || ["11:30", "19:30"]);
    setErrorMessage("");
    setIsAddModalOpen(true);
  };

  const handleSaveAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProjectId) return;
    setErrorMessage("");

    const cleanHandle = formHandle.trim();
    if (!cleanHandle) {
      setErrorMessage("Vui lòng nhập handle tài khoản (VD: @socnhotv)");
      return;
    }

    // Check duplicate handle on same platform locally
    const duplicate = accounts.some(
      (a) =>
        a.platform === formPlatform &&
        a.handle.toLowerCase() === cleanHandle.toLowerCase() &&
        (!editingAccount || a.id !== editingAccount.id)
    );

    if (duplicate) {
      setErrorMessage(`Tài khoản với handle "${cleanHandle}" trên nền tảng ${formPlatform.toUpperCase()} đã tồn tại!`);
      return;
    }

    setSaving(true);
    try {
      const payload = {
        platform: formPlatform,
        display_name: formDisplayName.trim() || cleanHandle,
        handle: cleanHandle,
        group: formGroup,
        auth_mode: formAuthMode,
        limits: { daily: formDailyLimit },
        golden_windows: formGoldenWindows,
      };

      const url = editingAccount
        ? `/core/projects/${activeProjectId}/social/accounts/${editingAccount.id}`
        : `/core/projects/${activeProjectId}/social/accounts`;
      const method = editingAccount ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Lỗi lưu tài khoản" }));
        throw new Error(err.detail || "Không thể lưu tài khoản");
      }

      setIsAddModalOpen(false);
      loadAccounts(activeProjectId);
      loadAccountsStats(activeProjectId);
      onRefresh?.();
    } catch (err: any) {
      setErrorMessage(err.message || "Đã xảy ra lỗi");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async (accId: string, accName: string) => {
    if (!activeProjectId) return;
    if (!confirm(`Bạn có chắc muốn xóa kênh "${accName}" khỏi danh sách tài khoản?`)) return;

    try {
      const res = await fetch(`/core/projects/${activeProjectId}/social/accounts/${accId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        loadAccounts(activeProjectId);
        loadAccountsStats(activeProjectId);
        onRefresh?.();
      }
    } catch {
      // Ignore
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      {/* Header with Account Count Pill */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-foreground">Quản Lý Kênh & Tài Khoản Mạng Xã Hội</h2>
            <span
              className={cn(
                "px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono",
                isFull
                  ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                  : "bg-primary/10 text-primary border border-primary/20"
              )}
            >
              {currentCount} / {maxAccounts} Tài khoản
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Kết nối kênh YouTube, TikTok, Facebook để lên lịch đăng tự động và theo dõi hạn ngạch
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={isFull}
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground font-medium text-xs hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="w-3.5 h-3.5" />
            Thêm tài khoản
          </button>
        </div>
      </div>

      {/* Grid of Accounts */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc) => {
          const stats = Array.isArray(accountsStats) ? accountsStats.find((s) => s.account_id === acc.id) : undefined;
          const isConnected = acc.status === "connected";

          return (
            <div
              key={acc.id}
              className="flex flex-col justify-between p-4 rounded-xl border border-border bg-card hover:border-border/80 transition-all space-y-3"
            >
              {/* Account Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {acc.avatar ? (
                    <img
                      src={acc.avatar}
                      alt={acc.display_name}
                      className="w-10 h-10 rounded-full border border-border object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                      {acc.display_name?.slice(0, 2).toUpperCase() || "AC"}
                    </div>
                  )}

                  <div>
                    <h3 className="font-semibold text-xs md:text-sm text-foreground line-clamp-1">
                      {acc.display_name}
                    </h3>
                    <p className="text-[11px] text-muted-foreground font-mono">{acc.handle}</p>
                  </div>
                </div>

                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/50">
                  {acc.platform}
                </span>
              </div>

              {/* Stats & Metadata */}
              <div className="space-y-1.5 text-xs border-t border-border/50 pt-2.5">
                <div className="flex justify-between text-muted-foreground text-[11px]">
                  <span>Trạng thái kết nối</span>
                  <span className={cn("font-medium", isConnected ? "text-emerald-400" : "text-zinc-400")}>
                    {isConnected ? "Đã kết nối OAuth" : "Gói đăng tay"}
                  </span>
                </div>

                <div className="flex justify-between text-muted-foreground text-[11px]">
                  <span>Bài tuần này</span>
                  <span className="font-semibold text-foreground font-mono">
                    {stats?.posts_this_week ?? 0} bài
                  </span>
                </div>

                {acc.golden_windows && acc.golden_windows.length > 0 && (
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-amber-500/90 flex items-center gap-1">
                      <Flame className="w-3 h-3" />
                      Giờ vàng
                    </span>
                    <span className="font-mono text-muted-foreground">
                      {acc.golden_windows.join(", ")}
                    </span>
                  </div>
                )}
              </div>

              {/* Actions Footer */}
              <div className="flex items-center justify-between pt-2 border-t border-border/50">
                <button
                  type="button"
                  onClick={() => handleOpenEdit(acc)}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  Sửa thiết lập
                </button>

                <button
                  type="button"
                  onClick={() => handleDeleteAccount(acc.id, acc.display_name)}
                  className="text-xs text-destructive hover:underline p-1"
                  aria-label="Xóa tài khoản"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}

        {/* Dashed Add Card (Hidden when full) */}
        {!isFull && (
          <button
            type="button"
            onClick={handleOpenAdd}
            className="flex flex-col items-center justify-center p-6 rounded-xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 transition-all min-h-[160px] text-center group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-full bg-muted group-hover:bg-primary/10 flex items-center justify-center text-muted-foreground group-hover:text-primary transition-colors mb-2">
              <Plus className="w-5 h-5" />
            </div>
            <span className="text-xs font-semibold text-foreground group-hover:text-primary">
              + Thêm tài khoản ({currentCount}/{maxAccounts})
            </span>
            <span className="text-[11px] text-muted-foreground mt-0.5">
              Thêm kênh YouTube, TikTok hoặc Facebook
            </span>
          </button>
        )}
      </div>

      {/* Add / Edit Account Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl bg-card border border-border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
              <h3 className="font-semibold text-sm text-foreground">
                {editingAccount ? "Chỉnh sửa Tài Khoản" : "Thêm Tài Khoản Mới"}
              </h3>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveAccount} className="p-5 space-y-4 text-xs">
              {errorMessage && (
                <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Platform */}
              <div>
                <label className="font-semibold text-foreground block mb-1">Nền tảng</label>
                <select
                  value={formPlatform}
                  onChange={(e) => setFormPlatform(e.target.value as PlatformType)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground focus:outline-none"
                >
                  <option value="youtube">YouTube</option>
                  <option value="tiktok">TikTok</option>
                  <option value="facebook">Facebook</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>

              {/* Display Name */}
              <div>
                <label className="font-semibold text-foreground block mb-1">Tên hiển thị</label>
                <input
                  type="text"
                  placeholder="VD: Sóc Nhỏ TV Official"
                  value={formDisplayName}
                  onChange={(e) => setFormDisplayName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none"
                />
              </div>

              {/* Handle */}
              <div>
                <label className="font-semibold text-foreground block mb-1">Handle / ID Kênh</label>
                <input
                  type="text"
                  required
                  placeholder="VD: @socnhotv_official"
                  value={formHandle}
                  onChange={(e) => setFormHandle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground font-mono placeholder:text-muted-foreground focus:outline-none"
                />
              </div>

              {/* Group */}
              <div>
                <label className="font-semibold text-foreground block mb-1">Nhóm kênh</label>
                <select
                  value={formGroup}
                  onChange={(e) => setFormGroup(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground focus:outline-none"
                >
                  <option value="official">Chính thức (Official)</option>
                  <option value="affiliate">Tiếp thị liên kết (Affiliate)</option>
                  <option value="seed">Nuôi nick / Seeding</option>
                </select>
              </div>

              {/* Daily Limit */}
              <div>
                <label className="font-semibold text-foreground block mb-1">Giới hạn bài đăng / ngày</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={formDailyLimit}
                  onChange={(e) => setFormDailyLimit(parseInt(e.target.value) || 3)}
                  className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-border bg-background text-foreground hover:bg-muted font-medium"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {saving ? "Đang lưu..." : editingAccount ? "Lưu thay đổi" : "Thêm tài khoản"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
