"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useLocale } from "next-intl";
import { CORE_URL } from "@/lib/repositories/core";
import { cn } from "@/lib/utils";
import {
  ChevronLeft,
  Key,
  Check,
  AlertTriangle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "@/components/ui/icons";

interface ProviderKeyStatus {
  provider: string;
  label: string;
  envVars: string[];
  configured: boolean;
  updatedAt?: string | null;
}

interface VerifyResult {
  valid: boolean;
  detail?: string | any;
}

export default function SettingsPage() {
  const locale = useLocale();
  const [providers, setProviders] = useState<ProviderKeyStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [verifying, setVerifying] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [verifyStatus, setVerifyStatus] = useState<Record<string, VerifyResult>>({});
  const [messages, setMessages] = useState<Record<string, { tone: "success" | "error"; text: string }>>({});

  // Nạp danh sách provider keys từ Core
  const loadKeyStatus = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${CORE_URL}/settings/api-keys`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list: ProviderKeyStatus[] = data.providers || [];
      // Lọc bỏ provider "local" vì local không cần API key
      const filtered = list.filter((p) => p.provider !== "local");
      setProviders(filtered);

      // Tự động kiểm tra trực tuyến (live verify) các provider đã configured
      // Để phát hiện ngay key hỏng/hết hạn và báo "Không hợp lệ"
      for (const p of filtered) {
        if (p.configured) {
          verifyProvider(p.provider, "");
        }
      }
    } catch (err: any) {
      console.error("Lỗi nạp danh sách key:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKeyStatus();
  }, [loadKeyStatus]);

  // Kiểm tra trực tuyến khóa API (Verify Live $0)
  const verifyProvider = async (provider: string, explicitKey?: string) => {
    setVerifying((prev) => ({ ...prev, [provider]: true }));
    setMessages((prev) => {
      const next = { ...prev };
      delete next[provider];
      return next;
    });

    try {
      const body: Record<string, any> = { provider };
      if (explicitKey && explicitKey.trim()) {
        body.apiKey = explicitKey.trim();
      }
      const res = await fetch(`${CORE_URL}/settings/api-keys/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json().catch(() => ({}));
      if (res.ok && data.valid) {
        setVerifyStatus((prev) => ({
          ...prev,
          [provider]: { valid: true, detail: "Khóa hợp lệ và đang hoạt động" },
        }));
      } else {
        const errorDetail =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message || "Khóa không hợp lệ hoặc đã hết hạn mức";
        setVerifyStatus((prev) => ({
          ...prev,
          [provider]: { valid: false, detail: errorDetail },
        }));
      }
    } catch (err: any) {
      setVerifyStatus((prev) => ({
        ...prev,
        [provider]: { valid: false, detail: String(err?.message || err) },
      }));
    } finally {
      setVerifying((prev) => ({ ...prev, [provider]: false }));
    }
  };

  // Lưu khóa API vào KeyVault
  const handleSaveKey = async (provider: string) => {
    const keyVal = inputValues[provider]?.trim();
    if (!keyVal) {
      setMessages((prev) => ({
        ...prev,
        [provider]: { tone: "error", text: "Vui lòng nhập khóa API trước khi lưu." },
      }));
      return;
    }

    setSaving((prev) => ({ ...prev, [provider]: true }));
    setMessages((prev) => {
      const next = { ...prev };
      delete next[provider];
      return next;
    });

    try {
      const res = await fetch(`${CORE_URL}/settings/api-keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          apiKey: keyVal,
          verifyLive: true,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Lỗi lưu khóa (HTTP ${res.status})`);
      }

      setMessages((prev) => ({
        ...prev,
        [provider]: { tone: "success", text: "Đã lưu và xác thực khóa thành công!" },
      }));

      // Xoá ô input để bảo mật và cập nhật trạng thái
      setInputValues((prev) => ({ ...prev, [provider]: "" }));
      // Cập nhật lại danh sách và trạng thái
      await loadKeyStatus();
    } catch (err: any) {
      setMessages((prev) => ({
        ...prev,
        [provider]: { tone: "error", text: String(err?.message || err) },
      }));
      setVerifyStatus((prev) => ({
        ...prev,
        [provider]: { valid: false, detail: String(err?.message || err) },
      }));
    } finally {
      setSaving((prev) => ({ ...prev, [provider]: false }));
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href={`/${locale}`}
              className="flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Quay lại Studio</span>
            </Link>
            <div className="h-4 w-px bg-border" />
            <h1 className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Key className="h-4 w-4 text-brand" />
              <span>Cài đặt & Khóa API Nhà cung cấp</span>
            </h1>
          </div>

          <button
            type="button"
            onClick={loadKeyStatus}
            disabled={loading}
            className="flex h-8 items-center gap-1.5 rounded-md border border-border px-2.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            <span>Làm mới</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 space-y-6">
        {/* Banner hướng dẫn */}
        <div className="rounded-xl border border-brand/20 bg-brand/5 p-4 sm:p-5 text-xs space-y-1.5">
          <div className="flex items-center gap-2 font-semibold text-brand text-sm">
            <Sparkles className="h-4 w-4" />
            <span>Quản lý khóa API bảo mật (KeyVault)</span>
          </div>
          <p className="text-muted-foreground leading-relaxed">
            Khóa API được lưu cục bộ trong máy chủ (`KeyVault`), không bao giờ bị lộ ra ngoài.
            Các nhà cung cấp được tích hợp theo Hợp đồng C1–C3. Bạn có thể kiểm tra trực tiếp (Verify Live)
            để đảm bảo hạn mức và tính hợp lệ trước khi chạy đồ thị.
          </p>
        </div>

        {/* Danh sách Provider */}
        <div className="space-y-4">
          {loading && providers.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground animate-pulse">
              Đang tải danh sách nhà cung cấp...
            </div>
          ) : (
            providers.map((p) => {
              const currentInput = inputValues[p.provider] || "";
              const isVerifying = verifying[p.provider];
              const isSaving = saving[p.provider];
              const vStatus = verifyStatus[p.provider];
              const msg = messages[p.provider];

              return (
                <div
                  key={p.provider}
                  className="rounded-xl border border-border bg-card p-4 sm:p-5 shadow-xs space-y-3"
                >
                  {/* Tên & Trạng thái */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground text-sm">{p.label}</span>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                          {p.provider}
                        </span>
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5 font-mono">
                        Biến môi trường: {p.envVars.join(", ") || "(Tùy chọn)"}
                      </div>
                    </div>

                    {/* Badge trạng thái */}
                    <div className="flex items-center gap-2">
                      {isVerifying ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full animate-pulse">
                          <RefreshCw className="h-3 w-3 animate-spin" /> Đang kiểm tra...
                        </span>
                      ) : vStatus ? (
                        vStatus.valid ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                            <ShieldCheck className="h-3.5 w-3.5" /> Hợp lệ
                          </span>
                        ) : (
                          <span
                            title={typeof vStatus.detail === "string" ? vStatus.detail : ""}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 dark:text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full"
                          >
                            <AlertTriangle className="h-3.5 w-3.5" /> Không hợp lệ
                          </span>
                        )
                      ) : p.configured ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          <Check className="h-3 w-3" /> Đã cấu hình
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground/70 bg-muted/40 px-2 py-0.5 rounded-full">
                          Chưa có key
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Chi tiết lỗi nếu không hợp lệ */}
                  {vStatus && !vStatus.valid && vStatus.detail && (
                    <div className="rounded-md border border-rose-500/20 bg-rose-500/5 p-2 text-[11px] text-rose-600 dark:text-rose-400">
                      <strong>Lỗi xác thực:</strong> {String(vStatus.detail)}
                    </div>
                  )}

                  {/* Input nhập key và các nút hành động */}
                  <div className="flex flex-col sm:flex-row gap-2 pt-1">
                    <div className="relative flex-1">
                      <input
                        type="password"
                        value={currentInput}
                        onChange={(e) =>
                          setInputValues((prev) => ({ ...prev, [p.provider]: e.target.value }))
                        }
                        placeholder={
                          p.configured
                            ? "Khóa hiện tại đã lưu. Nhập khóa mới để đổi..."
                            : `Nhập khóa API cho ${p.label}...`
                        }
                        className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground/50 focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                      />
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {/* Nút Kiểm tra key */}
                      <button
                        type="button"
                        disabled={isVerifying || (!p.configured && !currentInput)}
                        onClick={() => verifyProvider(p.provider, currentInput)}
                        className="flex h-8 items-center gap-1 rounded-lg border border-border bg-muted/50 px-2.5 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50 transition-colors"
                      >
                        <RefreshCw className={cn("h-3 w-3", isVerifying && "animate-spin")} />
                        <span>Kiểm tra key</span>
                      </button>

                      {/* Nút Lưu khóa */}
                      <button
                        type="button"
                        disabled={isSaving || !currentInput}
                        onClick={() => handleSaveKey(p.provider)}
                        className="flex h-8 items-center gap-1 rounded-lg bg-brand px-3 text-xs font-medium text-brand-foreground hover:bg-brand/90 disabled:opacity-50 transition-colors"
                      >
                        {isSaving ? "Đang lưu..." : "Lưu khóa"}
                      </button>
                    </div>
                  </div>

                  {/* Thông báo kết quả lưu */}
                  {msg && (
                    <p
                      className={cn(
                        "text-[11px] font-medium pt-0.5",
                        msg.tone === "success"
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-rose-600 dark:text-rose-400"
                      )}
                    >
                      {msg.text}
                    </p>
                  )}
                </div>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}
