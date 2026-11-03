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
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Upload,
  Key,
  ChevronRight,
  Globe,
  Sun,
  Moon,
  Laptop,
  Maximize2,
  DollarSign,
  Database,
  Trash2,
  ListOrdered,
} from "@/components/ui/icons";

const PROVIDERS: Array<{ id: ProviderKeyId; label: string }> = [
  { id: "gemini", label: "Google Gemini / Veo" },
  { id: "fal", label: "fal.ai (LTX / Flux)" },
  { id: "openai", label: "OpenAI" },
  { id: "replicate", label: "Replicate" },
];

export function UserBubble({
  compact = false,
  placement = "above",
}: {
  compact?: boolean;
  placement?: "above" | "below" | "aboveLeft" | "beside";
}) {
  const t = useTranslations("userBubble");
  const c = useTranslations("common");
  const locale = useLocale() as "vi" | "en";
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  const {
    aspectRatio,
    setAspectRatio,
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
  const [section, setSection] = useState<string | null>(null);
  const [editingKeyProvider, setEditingKeyProvider] =
    useState<ProviderKeyId | null>(null);
  const [keyInputValue, setKeyInputValue] = useState("");
  const [clearStep, setClearStep] = useState<0 | 1 | 2>(0);

  const rootRef = useRef<HTMLDivElement>(null);
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

    const handleMouseDown = (e: Event) => {
      const target = e.target as Node;
      if (rootRef.current && !rootRef.current.contains(target)) {
        setOpen(false);
        setEditingKeyProvider(null);
        setClearStep(0);
      }
    };

    document.addEventListener("keydown", handleKeyDown, true);
    document.addEventListener("pointerdown", handleMouseDown, true);
    return () => {
      document.removeEventListener("keydown", handleKeyDown, true);
      document.removeEventListener("pointerdown", handleMouseDown, true);
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

  const seg = <T extends string>(
    items: { id: T; label: React.ReactNode }[],
    value: T,
    onChange: (v: T) => void
  ) => (
    <div className="flex rounded-md border border-border bg-card p-0.5">
      {items.map((it) => (
        <button
          key={it.id}
          type="button"
          onClick={() => onChange(it.id)}
          className={cn(
            "flex h-7 flex-1 items-center justify-center rounded px-2 text-xs font-medium transition-colors active:scale-95",
            value === it.id ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {it.label}
        </button>
      ))}
    </div>
  );

  const keysConfigured = PROVIDERS.filter((p) => apiKeyStatus[p.id]?.configured).length;
  const ThemeIcon = theme === "dark" ? Moon : theme === "light" ? Sun : Laptop;
  const inputCls = "h-7 w-full rounded-md border border-border bg-card px-2 text-xs tnum text-foreground";

  const rows: { id: string; icon: React.ReactNode; label: string; summary: string; detail: React.ReactNode }[] = [
    {
      id: "profile",
      icon: userProfile.avatarDataUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={userProfile.avatarDataUrl} alt="" className="h-6 w-6 rounded-full object-cover object-top" />
      ) : (
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-[10px] font-semibold text-foreground">{initials}</span>
      ),
      label: userProfile.name,
      summary: userProfile.email,
      detail: (
        <>
          <input type="text" value={userProfile.name} onChange={(e) => setUserProfile({ name: e.target.value })} aria-label={t("title")} className={inputCls} />
          <input type="email" value={userProfile.email} onChange={(e) => setUserProfile({ email: e.target.value })} className={inputCls} />
          <button type="button" onClick={() => fileInputRef.current?.click()} className="flex h-7 items-center gap-1.5 rounded-md border border-border bg-card px-2 text-foreground hover:bg-accent">
            <Upload className="h-3 w-3" />
            <span>{t("uploadAvatar")}</span>
          </button>
        </>
      ),
    },
    {
      id: "language",
      icon: <Globe className="h-4 w-4" />,
      label: t("languageLabel"),
      summary: locale.toUpperCase(),
      detail: seg(
        [
          { id: "vi" as const, label: "Tiếng Việt" },
          { id: "en" as const, label: "English" },
        ],
        locale,
        (l) => router.replace(pathname, { locale: l })
      ),
    },
    {
      id: "theme",
      icon: <ThemeIcon className="h-4 w-4" />,
      label: t("themeLabel"),
      summary: theme === "light" ? t("themeLight") : theme === "dark" ? t("themeDark") : t("themeSystem"),
      detail: seg(
        [
          { id: "light" as const, label: <span className="flex items-center gap-1"><Sun className="h-3.5 w-3.5" />{t("themeLight")}</span> },
          { id: "dark" as const, label: <span className="flex items-center gap-1"><Moon className="h-3.5 w-3.5" />{t("themeDark")}</span> },
          { id: "system" as const, label: <span className="flex items-center gap-1"><Laptop className="h-3.5 w-3.5" />{t("themeSystem")}</span> },
        ],
        theme as "light" | "dark" | "system",
        (v) => setTheme(v)
      ),
    },
    {
      id: "aspect",
      icon: <Maximize2 className="h-4 w-4" />,
      label: "Tỉ lệ khung hình",
      summary: aspectRatio,
      detail: seg(
        (["9:16", "16:9", "1:1", "4:5"] as const).map((r) => ({ id: r, label: r })),
        aspectRatio,
        (r) => setAspectRatio(r)
      ),
    },
    {
      id: "run",
      icon: <DollarSign className="h-4 w-4" />,
      label: t("spendingTitle"),
      summary: `${isMockMode ? "Mock" : "Live"} · $${perRunSpendingLimitUsd}/${dailySpendingLimitUsd}`,
      detail: (
        <>
          {seg(
            [
              { id: "mock" as const, label: t("mockModeOn") },
              { id: "live" as const, label: t("mockModeOff") },
            ],
            isMockMode ? "mock" : "live",
            (v) => setIsMockMode(v === "mock")
          )}
          <div className="grid grid-cols-2 gap-2">
            <label className="space-y-1">
              <span className="block text-muted-foreground">{t("perRunLimit")}</span>
              <input type="number" step="0.5" min="0.1" value={perRunSpendingLimitUsd} onChange={(e) => setPerRunSpendingLimitUsd(Number(e.target.value) || 1.0)} className={inputCls} />
            </label>
            <label className="space-y-1">
              <span className="block text-muted-foreground">{t("dailyLimit")}</span>
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
                className={inputCls}
              />
            </label>
          </div>
        </>
      ),
    },
    {
      id: "keys",
      icon: <Key className="h-4 w-4" />,
      label: t("apiKeysTitle"),
      summary: `${keysConfigured}/${PROVIDERS.length}`,
      detail: (
        <>
          <ul className="space-y-1.5">
            {PROVIDERS.map((p) => {
              const st = apiKeyStatus[p.id];
              return (
                <li key={p.id} className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 truncate text-muted-foreground">
                    <span className={cn("h-2 w-2 rounded-full", st?.configured ? "bg-semantic-success" : "bg-border")} title={st?.configured ? t("keyConfigured") : t("keyMissing")} />
                    {p.label}
                  </span>
                  <button
                    type="button"
                    title={t("enterKeyBtn")}
                    aria-label={`${t("enterKeyBtn")}: ${p.label}`}
                    onClick={() => {
                      setEditingKeyProvider(p.id);
                      setKeyInputValue("");
                    }}
                    className="flex h-6 w-6 items-center justify-center rounded border border-border bg-card text-foreground hover:bg-accent"
                  >
                    <Key className="h-3 w-3" />
                  </button>
                </li>
              );
            })}
          </ul>
          {editingKeyProvider && (
            <div className="space-y-2 rounded-md border border-border bg-card p-2">
              <p className="font-medium text-foreground">{t("keyModalTitle", { provider: editingKeyProvider.toUpperCase() })}</p>
              <p className="leading-snug text-muted-foreground">{t("keyModalNote")}</p>
              <input type="password" autoComplete="off" value={keyInputValue} onChange={(e) => setKeyInputValue(e.target.value)} placeholder={t("keyPlaceholder")} className="h-7 w-full rounded border border-border bg-background px-2 font-mono text-xs text-foreground" />
              <div className="flex justify-end gap-1.5">
                <button type="button" onClick={() => { setEditingKeyProvider(null); setKeyInputValue(""); }} className="h-6 rounded border border-border px-2 text-muted-foreground hover:text-foreground">{c("cancel")}</button>
                <button type="button" onClick={handleSaveApiKey} className="h-6 rounded bg-primary px-2.5 font-medium text-primary-foreground">{t("saveKeyBtn")}</button>
              </div>
            </div>
          )}
        </>
      ),
    },
    {
      id: "storage",
      icon: <Database className="h-4 w-4" />,
      label: t("storageTitle"),
      summary: formattedStorage,
      detail: (
        <>
          <select value={storageBackend} onChange={(e) => setStorageBackend(e.target.value as "local" | "supabase")} className={inputCls}>
            <option value="local">{t("storageLocal")}</option>
            <option value="supabase">{t("storageSupabase")}</option>
          </select>
          <p className="text-muted-foreground">{t("storageUsed", { size: formattedStorage })} · IndexedDB / JSON</p>
          {clearStep === 0 ? (
            <button type="button" onClick={handleClearLocalData} className="flex h-7 w-full items-center justify-center gap-1.5 rounded-md border border-border bg-card px-2 text-semantic-danger hover:bg-accent">
              <Trash2 className="h-3.5 w-3.5" />
              <span>{t("clearDataBtn")}</span>
            </button>
          ) : (
            <div className="space-y-1.5 rounded-md border border-semantic-danger/40 bg-card p-2">
              <p className="font-medium text-semantic-danger">{clearStep === 1 ? t("clearStep1") : t("clearStep2")}</p>
              <div className="flex gap-1.5">
                <button type="button" onClick={() => setClearStep(0)} className="h-6 flex-1 rounded border border-border px-2 text-foreground">{t("clearCancel")}</button>
                <button type="button" onClick={handleClearLocalData} className="h-6 flex-1 rounded bg-semantic-danger px-2 font-medium text-white">{c("confirm")}</button>
              </div>
            </div>
          )}
        </>
      ),
    },
    {
      id: "core",
      icon: <span className={cn("h-2.5 w-2.5 rounded-full", coreHealth.online ? "bg-semantic-success" : "bg-semantic-danger")} />,
      label: t("coreStatusTitle"),
      summary: coreHealth.online ? `v${coreHealth.version}` : "offline",
      detail: (
        <p className={cn("tnum font-medium", coreHealth.online ? "text-semantic-success" : "text-semantic-danger")}>
          {coreHealth.online ? t("coreOnline", { version: coreHealth.version }) : t("coreOffline")}
        </p>
      ),
    },
    {
      id: "shortcuts",
      icon: <ListOrdered className="h-4 w-4" />,
      label: t("shortcutsTitle"),
      summary: "",
      detail: (
        <dl className="space-y-1">
          {[
            [t("shortcutRun"), "Enter"],
            [t("shortcutDuplicate"), "Ctrl+D"],
            [t("shortcutDelete"), "Delete"],
            [t("shortcutUndo"), "Ctrl+Z / Ctrl+Shift+Z"],
            [t("shortcutPanel"), "Ctrl+B"],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2">
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="font-mono text-foreground">{v}</dd>
            </div>
          ))}
        </dl>
      ),
    },
  ];

  // "beside": avatar tròn và thẻ cài đặt là MỘT khối, tự to ra từ avatar
  const merged = placement === "beside";
  const Shell: any = merged ? motion.div : React.Fragment;
  const shellProps = merged
    ? {
        initial: false,
        animate: { width: open ? 316 : 48 },
        transition: { duration: 0.24, ease: [0.22, 1, 0.36, 1] },
        className: "absolute bottom-0 left-0 flex flex-col-reverse overflow-hidden rounded-3xl border border-border bg-card",
      }
    : {};

  const Row: any = merged ? "div" : React.Fragment;
  const rowProps = merged ? { className: cn("flex shrink-0 items-center", open && "border-t border-border") } : {};

  return (
    <div ref={rootRef} className={cn("relative", merged && "h-12 w-12")}>
      <Shell {...shellProps}>
      <Row {...rowProps}>
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
          "flex shrink-0 items-center gap-2 rounded-full text-left transition-colors hover:bg-accent",
          !merged && "border border-border bg-card",
          compact ? "h-12 w-12 justify-center" : "h-9 w-full px-1.5 pr-2.5"
        )}
      >
        {userProfile.avatarDataUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={userProfile.avatarDataUrl}
            alt={userProfile.name}
            className={cn("shrink-0 rounded-full object-cover object-top", compact ? "h-10 w-10" : "h-7 w-7")}
          />
        ) : (
          <span className={cn("flex shrink-0 items-center justify-center rounded-full bg-accent font-semibold text-foreground", compact ? "h-10 w-10 text-sm" : "h-7 w-7 text-xs")}>
            {initials}
          </span>
        )}
        {!compact && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-foreground">
              {userProfile.name}
            </p>
            <p className="truncate text-[13px] text-muted-foreground">
              {coreHealth.online ? `Core v${coreHealth.version}` : "Mock UI"}
            </p>
          </div>
        )}
      </button>
      {merged && (
        <AnimatePresence initial={false}>
          {open && (
            <motion.button
              key="infobar"
              type="button"
              title="Sửa hồ sơ"
              aria-label="Sửa hồ sơ"
              aria-expanded={section === "profile"}
              onClick={() => setSection((v) => (v === "profile" ? null : "profile"))}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1, transition: { delay: 0.1, duration: 0.15 } }}
              exit={{ opacity: 0, transition: { duration: 0.05 } }}
              className="mr-2 min-w-0 flex-1 rounded-xl px-2 py-1.5 text-left leading-tight transition-colors hover:bg-accent"
            >
              <p className="truncate text-[13px] font-medium text-foreground">{userProfile.name}</p>
              <p className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
                <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", coreHealth.online ? "bg-semantic-success" : "bg-muted-foreground")} />
                {coreHealth.online ? `Core v${coreHealth.version}` : "Core offline"}
              </p>
            </motion.button>
          )}
        </AnimatePresence>
      )}
      </Row>

      <AnimatePresence>
        {open && (
          <motion.div
            ref={popoverRef}
            role="dialog"
            aria-modal="true"
            aria-label={t("title")}
            initial={merged ? { height: 0, opacity: 0 } : { opacity: 0, y: 8, scale: 0.97 }}
            animate={merged ? { height: "auto", opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
            exit={merged ? { height: 0, opacity: 0 } : { opacity: 0, y: 8, scale: 0.97 }}
            transition={{ duration: merged ? 0.24 : 0.16, ease: "easeOut" }}
            className={cn(
              merged
                ? "w-[316px] max-h-[70dvh] overflow-y-auto scroll-quiet p-2 text-popover-foreground"
                : "fixed md:absolute z-50 w-[300px] max-h-[82dvh] overflow-y-auto scroll-quiet rounded-[12px] border border-border bg-popover p-2 text-popover-foreground",
              merged
                ? ""
                : placement === "below"
                ? "right-0 top-11"
                : placement === "aboveLeft"
                ? "bottom-11 left-0"
                : compact
                ? "bottom-16 right-3"
                : "bottom-11 left-0"
            )}
          >
            <div className="flex items-center justify-between px-2 pb-1.5 pt-1">
              <h2 className="text-sm font-semibold">{t("title")}</h2>
            </div>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleAvatarUpload} className="hidden" />

            <ul className="space-y-0.5">
              {rows.filter((r) => !["profile", "core", "shortcuts"].includes(r.id)).map((row) => {
                const isOpen = section === row.id;
                return (
                  <li key={row.id} className="rounded-lg">
                    <button
                      type="button"
                      aria-expanded={isOpen}
                      onClick={() => setSection(isOpen ? null : row.id)}
                      className={cn(
                        "flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left transition-colors hover:bg-accent",
                        isOpen && "bg-accent"
                      )}
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center text-muted-foreground">
                        {row.icon}
                      </span>
                      <span className="min-w-0 flex-1 truncate text-[13px] font-medium text-foreground">{row.label}</span>
                      <span className="max-w-[110px] truncate text-xs text-muted-foreground tnum">{row.summary}</span>
                      <ChevronRight className={cn("h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform", isOpen && "rotate-90")} />
                    </button>
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.18 }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-2 px-2 pb-2.5 pt-1.5 text-xs">{row.detail}</div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </li>
                );
              })}
            </ul>
            {/* Hồ sơ: mở ngay sát thanh thông tin ở đáy khối */}
            <AnimatePresence initial={false}>
              {section === "profile" && (
                <motion.div
                  key="profile-editor"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.18 }}
                  className="overflow-hidden"
                >
                  <div className="mt-1 space-y-2 border-t border-border px-2 pb-1 pt-3 text-xs">{rows.find((r) => r.id === "profile")?.detail}</div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
      </Shell>
    </div>
  );
}
