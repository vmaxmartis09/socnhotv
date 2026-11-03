"use client";

import React, { useEffect, useRef, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";
import { useTheme } from "@/components/theme/ThemeProvider";
import { useStudioStore } from "@/store";
import type { ProviderKeyId } from "@/store/slices/userSettingsSlice";
import { checkCoreHealth } from "@/lib/core-api";
import { CORE_URL } from "@/lib/repositories/core";
import { cn } from "@/lib/utils";
import { X, Upload, Key } from "@/components/ui/icons";

const PROVIDERS: Array<{ id: ProviderKeyId; label: string }> = [
  { id: "gemini", label: "Google Gemini / Veo" },
  { id: "fal", label: "fal.ai (LTX / Flux)" },
  { id: "openai", label: "OpenAI" },
  { id: "replicate", label: "Replicate" },
];

export function UserBubble({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("userBubble");
  const c = useTranslations("common");
  const locale = useLocale() as "vi" | "en";
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  const {
    activeProjectId,
    isMockMode,
    setIsMockMode,
    userProfile,
    setUserProfile,
    perRunSpendingLimitUsd,
    setPerRunSpendingLimitUsd,
    dailySpendingLimitUsd,
    setDailySpendingLimitUsd,
    setSpendingLimitUsd,
    storageBackend,
    setStorageBackend,
    storageUsedBytes,
    setStorageUsedBytes,
    apiKeyStatus,
    setProviderKeyConfigured,
    coreHealth,
    setCoreHealth,
  } = useStudioStore();

  const [open, setOpen] = useState(false);
  const [editingKeyProvider, setEditingKeyProvider] =
    useState<ProviderKeyId | null>(null);
  const [keyInputValue, setKeyInputValue] = useState("");
  const [clearStep, setClearStep] = useState<0 | 1 | 2>(0);

  const triggerRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync Core health & storage estimate when opened
  useEffect(() => {
    if (!open) return;
    let active = true;
    checkCoreHealth().then((h) => {
      if (active) setCoreHealth({ ...h, checkedAt: new Date().toISOString() });
    });
    fetch(`${CORE_URL}/settings/api-keys`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!active || !data?.providers) return;
        for (const p of PROVIDERS) {
          const info = data.providers[p.id];
          if (info) {
            setProviderKeyConfigured(
              p.id,
              Boolean(info.configured),
              info.updatedAt
            );
          }
        }
      })
      .catch(() => {});

    if (typeof window !== "undefined") {
      try {
        let total = 0;
        for (let i = 0; i < window.localStorage.length; i++) {
          const k = window.localStorage.key(i) || "";
          const v = window.localStorage.getItem(k) || "";
          total += (k.length + v.length) * 2;
        }
        setStorageUsedBytes(Math.max(total, 48120));
      } catch {
        // ignore
      }
    }
    return () => {
      active = false;
    };
  }, [open, setCoreHealth, setProviderKeyConfigured, setStorageUsedBytes]);

  // Escape & outside-click + focus trap
  useEffect(() => {
    if (!open) return;
    const prevFocused = document.activeElement as HTMLElement | null;
    const focusables = popoverRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusables?.[0]?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        if (editingKeyProvider) {
          setEditingKeyProvider(null);
          setKeyInputValue("");
        } else {
          setOpen(false);
          triggerRef.current?.focus();
        }
        return;
      }
      if (e.key === "Tab" && popoverRef.current) {
        const nodes = popoverRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (nodes.length === 0) return;
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    const handleMouseDown = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        popoverRef.current &&
        !popoverRef.current.contains(target) &&
        triggerRef.current &&
        !triggerRef.current.contains(target)
      ) {
        setOpen(false);
        setEditingKeyProvider(null);
        setClearStep(0);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleMouseDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleMouseDown);
      prevFocused?.focus?.();
    };
  }, [open, editingKeyProvider]);

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setUserProfile({ avatarDataUrl: reader.result });
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSaveApiKey = async () => {
    if (!editingKeyProvider || !keyInputValue.trim()) return;
    const provider = editingKeyProvider;
    const secret = keyInputValue.trim();
    // Wipe input immediately so key is never shown again
    setKeyInputValue("");
    setEditingKeyProvider(null);
    setProviderKeyConfigured(provider, true, new Date().toISOString());
    try {
      await fetch(`${CORE_URL}/settings/api-keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, apiKey: secret }),
      });
    } catch {
      // Stored locally in configured status flag
    }
  };

  const handleClearLocalData = () => {
    if (clearStep === 0) {
      setClearStep(1);
      return;
    }
    if (clearStep === 1) {
      setClearStep(2);
      return;
    }
    if (typeof window !== "undefined") {
      window.localStorage.clear();
      window.location.reload();
    }
  };

  const initials = (userProfile.name || "S")
    .split(" ")
    .map((w) => w.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const formattedStorage = `${(storageUsedBytes / 1024).toFixed(1)} KB`;

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => {
          setOpen((v) => !v);
          setClearStep(0);
          setEditingKeyProvider(null);
        }}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={t("triggerLabel")}
        className={cn(
          "flex items-center gap-2 rounded-full border border-border bg-card text-left transition-colors hover:bg-accent",
          compact ? "h-9 w-9 justify-center" : "h-9 w-full px-1.5 pr-2.5"
        )}
      >
        {userProfile.avatarDataUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={userProfile.avatarDataUrl}
            alt={userProfile.name}
            className="h-7 w-7 shrink-0 rounded-full object-cover object-top"
          />
        ) : (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-foreground">
            {initials}
          </span>
        )}
        {!compact && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-foreground">
              {userProfile.name}
            </p>
            <p className="truncate text-[11px] text-muted-foreground">
              {coreHealth.online ? `Core v${coreHealth.version}` : "Mock UI"}
            </p>
          </div>
        )}
      </button>

      {open && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-modal="true"
          aria-label={t("title")}
          className={cn(
            "fixed md:absolute z-50 w-[320px] max-h-[82dvh] overflow-y-auto rounded-[12px] border border-border bg-popover p-3.5 text-popover-foreground",
            compact
              ? "bottom-16 right-3"
              : "bottom-11 left-0"
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <h2 className="text-sm font-semibold">{t("title")}</h2>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label={c("close")}
              className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Profile & Workspace */}
          <div className="mt-3 flex items-center gap-2.5 border-b border-border pb-3">
            <div className="relative shrink-0">
              {userProfile.avatarDataUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={userProfile.avatarDataUrl}
                  alt={userProfile.name}
                  className="h-10 w-10 rounded-full border border-border object-cover object-top"
                />
              ) : (
                <span className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-accent text-xs font-semibold">
                  {initials}
                </span>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                className="hidden"
              />
            </div>
            <div className="min-w-0 flex-1 space-y-1">
              <input
                type="text"
                value={userProfile.name}
                onChange={(e) => setUserProfile({ name: e.target.value })}
                aria-label={t("title")}
                className="h-6 w-full rounded border border-transparent bg-transparent px-1 text-xs font-semibold text-foreground hover:border-border focus:border-border"
              />
              <input
                type="email"
                value={userProfile.email}
                onChange={(e) => setUserProfile({ email: e.target.value })}
                className="h-5 w-full rounded border border-transparent bg-transparent px-1 text-[11px] text-muted-foreground hover:border-border focus:border-border"
              />
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex h-7 items-center gap-1 rounded-md border border-border bg-card px-2 text-[11px] text-foreground hover:bg-accent"
            >
              <Upload className="h-3 w-3" />
              <span>{t("uploadAvatar")}</span>
            </button>
          </div>

          {/* Active workspace, Language, Theme */}
          <div className="mt-3 space-y-2.5 border-b border-border pb-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("workspaceLabel")}</span>
              <code className="rounded bg-accent px-1.5 py-0.5 font-mono text-[11px] text-foreground">
                {activeProjectId}
              </code>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("languageLabel")}</span>
              <div className="flex rounded-md border border-border bg-card p-0.5">
                {(["vi", "en"] as const).map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => router.replace(pathname, { locale: l })}
                    className={cn(
                      "h-6 rounded px-2 text-xs font-medium transition-colors",
                      locale === l
                        ? "bg-accent text-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {l === "vi" ? "Tiếng Việt" : "English"}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("themeLabel")}</span>
              <div className="flex rounded-md border border-border bg-card p-0.5">
                {(
                  [
                    { id: "light", label: t("themeLight") },
                    { id: "dark", label: t("themeDark") },
                    { id: "system", label: t("themeSystem") },
                  ] as const
                ).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setTheme(item.id)}
                    className={cn(
                      "h-6 rounded px-2 text-xs font-medium transition-colors",
                      theme === item.id
                        ? "bg-accent text-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Spending limits & Mock mode */}
          <div className="mt-3 space-y-2 border-b border-border pb-3 text-xs">
            <p className="font-medium text-foreground">{t("spendingTitle")}</p>
            <div className="grid grid-cols-2 gap-2">
              <label className="space-y-1">
                <span className="block text-[11px] text-muted-foreground">
                  {t("perRunLimit")}
                </span>
                <input
                  type="number"
                  step="0.5"
                  min="0.1"
                  value={perRunSpendingLimitUsd}
                  onChange={(e) =>
                    setPerRunSpendingLimitUsd(Number(e.target.value) || 1.0)
                  }
                  className="h-7 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
                />
              </label>
              <label className="space-y-1">
                <span className="block text-[11px] text-muted-foreground">
                  {t("dailyLimit")}
                </span>
                <input
                  type="number"
                  step="1"
                  min="1"
                  value={dailySpendingLimitUsd}
                  onChange={(e) => {
                    const v = Number(e.target.value) || 5.0;
                    setDailySpendingLimitUsd(v);
                    setSpendingLimitUsd(v);
                  }}
                  className="h-7 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground"
                />
              </label>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-muted-foreground">{t("mockModeLabel")}</span>
              <button
                type="button"
                role="switch"
                aria-checked={isMockMode}
                onClick={() => setIsMockMode(!isMockMode)}
                className={cn(
                  "h-6 rounded-md border px-2 text-xs font-medium transition-colors",
                  isMockMode
                    ? "border-brand text-brand bg-card"
                    : "border-border text-muted-foreground bg-card"
                )}
              >
                {isMockMode ? t("mockModeOn") : t("mockModeOff")}
              </button>
            </div>
          </div>

          {/* API Keys per provider (write-only, never shown again) */}
          <div className="mt-3 space-y-2 border-b border-border pb-3 text-xs">
            <p className="font-medium text-foreground">{t("apiKeysTitle")}</p>
            <ul className="space-y-1.5">
              {PROVIDERS.map((p) => {
                const st = apiKeyStatus[p.id];
                return (
                  <li
                    key={p.id}
                    className="flex items-center justify-between gap-2"
                  >
                    <span className="truncate text-muted-foreground">
                      {p.label}
                    </span>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span
                        className={cn(
                          "text-[11px] font-medium",
                          st?.configured
                            ? "text-semantic-success"
                            : "text-muted-foreground"
                        )}
                      >
                        {st?.configured ? t("keyConfigured") : t("keyMissing")}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingKeyProvider(p.id);
                          setKeyInputValue("");
                        }}
                        className="flex h-6 items-center gap-1 rounded border border-border bg-card px-1.5 text-[11px] text-foreground hover:bg-accent"
                      >
                        <Key className="h-3 w-3" />
                        <span>{t("enterKeyBtn")}</span>
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>

            {editingKeyProvider && (
              <div className="mt-2 rounded-md border border-border bg-card p-2 space-y-2">
                <p className="text-[11px] font-medium text-foreground">
                  {t("keyModalTitle", {
                    provider: editingKeyProvider.toUpperCase(),
                  })}
                </p>
                <p className="text-[11px] text-muted-foreground leading-snug">
                  {t("keyModalNote")}
                </p>
                <input
                  type="password"
                  autoComplete="off"
                  value={keyInputValue}
                  onChange={(e) => setKeyInputValue(e.target.value)}
                  placeholder={t("keyPlaceholder")}
                  className="h-7 w-full rounded border border-border bg-background px-2 font-mono text-xs text-foreground"
                />
                <div className="flex justify-end gap-1.5">
                  <button
                    type="button"
                    onClick={() => {
                      setEditingKeyProvider(null);
                      setKeyInputValue("");
                    }}
                    className="h-6 rounded border border-border px-2 text-[11px] text-muted-foreground hover:text-foreground"
                  >
                    {c("cancel")}
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveApiKey}
                    className="h-6 rounded bg-primary px-2.5 text-[11px] font-medium text-primary-foreground"
                  >
                    {t("saveKeyBtn")}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Data storage & Core connection status */}
          <div className="mt-3 space-y-2 border-b border-border pb-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">{t("storageTitle")}</span>
              <select
                value={storageBackend}
                onChange={(e) =>
                  setStorageBackend(e.target.value as "local" | "supabase")
                }
                className="h-6 rounded border border-border bg-card px-1.5 text-xs text-foreground"
              >
                <option value="local">{t("storageLocal")}</option>
                <option value="supabase">{t("storageSupabase")}</option>
              </select>
            </div>
            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span>{t("storageUsed", { size: formattedStorage })}</span>
              <span className="tnum">IndexedDB / JSON</span>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-muted-foreground">
                {t("coreStatusTitle")}
              </span>
              <span
                className={cn(
                  "text-xs font-medium tnum",
                  coreHealth.online
                    ? "text-semantic-success"
                    : "text-semantic-danger"
                )}
              >
                {coreHealth.online
                  ? t("coreOnline", { version: coreHealth.version })
                  : t("coreOffline")}
              </span>
            </div>
          </div>

          {/* Keyboard shortcuts */}
          <div className="mt-3 space-y-1.5 border-b border-border pb-3 text-xs">
            <p className="font-medium text-foreground">{t("shortcutsTitle")}</p>
            <dl className="space-y-1 text-[11px]">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t("shortcutRun")}</dt>
                <dd className="font-mono text-foreground">Enter</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">
                  {t("shortcutDuplicate")}
                </dt>
                <dd className="font-mono text-foreground">Ctrl+D</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t("shortcutDelete")}</dt>
                <dd className="font-mono text-foreground">Delete</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t("shortcutUndo")}</dt>
                <dd className="font-mono text-foreground">
                  Ctrl+Z / Ctrl+Shift+Z
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t("shortcutPanel")}</dt>
                <dd className="font-mono text-foreground">Ctrl+B</dd>
              </div>
            </dl>
          </div>

          {/* 2-step Clear local data */}
          <div className="mt-3 pt-0.5">
            {clearStep === 0 ? (
              <button
                type="button"
                onClick={handleClearLocalData}
                className="h-7 w-full rounded-md border border-border bg-card px-2 text-xs text-semantic-danger hover:bg-accent"
              >
                {t("clearDataBtn")}
              </button>
            ) : (
              <div className="space-y-1.5 rounded-md border border-semantic-danger/40 bg-card p-2">
                <p className="text-[11px] font-medium text-semantic-danger">
                  {clearStep === 1 ? t("clearStep1") : t("clearStep2")}
                </p>
                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => setClearStep(0)}
                    className="h-6 flex-1 rounded border border-border px-2 text-[11px] text-foreground"
                  >
                    {t("clearCancel")}
                  </button>
                  <button
                    type="button"
                    onClick={handleClearLocalData}
                    className="h-6 flex-1 rounded bg-semantic-danger px-2 text-[11px] font-medium text-white"
                  >
                    {c("confirm")}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
