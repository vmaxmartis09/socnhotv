"use client";

import React from "react";
import { useSocialStore } from "@/store/modules/social";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Clock,
  Sparkles,
  X,
  Zap,
} from "./icons";

interface NotificationDrawerProps {
  projectId: string;
}

export function NotificationDrawer({ projectId }: NotificationDrawerProps) {
  const {
    notifications,
    unreadNotifCount,
    isNotifDrawerOpen,
    setNotifDrawerOpen,
    markNotificationRead,
    clearNotifications,
    setActiveTab,
  } = useSocialStore();

  if (!isNotifDrawerOpen) return null;

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "publish_success":
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case "publish_failed":
        return <AlertTriangle className="w-5 h-5 text-rose-500" />;
      case "token_expired":
        return <Zap className="w-5 h-5 text-amber-500" />;
      case "schedule_gap":
        return <Clock className="w-5 h-5 text-indigo-500" />;
      default:
        return <Sparkles className="w-5 h-5 text-cyan-500" />;
    }
  };

  const handleAction = (notif: any) => {
    markNotificationRead(projectId, notif.id);
    if (notif.action_url) {
      if (notif.action_url.includes("tab=")) {
        const tab = notif.action_url.split("tab=")[1].split("&")[0];
        setActiveTab(tab as any);
      }
      setNotifDrawerOpen(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={() => setNotifDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white dark:bg-zinc-900 shadow-2xl flex flex-col border-l border-zinc-200 dark:border-zinc-800">
          {/* Header */}
          <div className="p-5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-zinc-900 dark:text-white">
                  Thông báo Social
                </h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  {unreadNotifCount} thông báo chưa đọc
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {notifications.length > 0 && (
                <button
                  onClick={() => clearNotifications(projectId)}
                  className="text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 font-medium px-2 py-1"
                >
                  Xoá tất cả
                </button>
              )}
              <button
                onClick={() => setNotifDrawerOpen(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {notifications.length === 0 ? (
              <div className="text-center py-16 text-zinc-400">
                <Bell className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Không có thông báo nào</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => handleAction(notif)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer flex gap-3 ${
                    notif.read
                      ? "bg-zinc-50/50 dark:bg-zinc-800/30 border-zinc-200/60 dark:border-zinc-800/60 opacity-80"
                      : "bg-white dark:bg-zinc-800 border-indigo-200 dark:border-indigo-800/50 shadow-sm"
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">{getTypeIcon(notif.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-zinc-900 dark:text-white truncate">
                        {notif.title}
                      </p>
                      {!notif.read && (
                        <span className="w-2 h-2 rounded-full bg-indigo-600 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-1 line-clamp-2">
                      {notif.message}
                    </p>
                    <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-2">
                      {new Date(notif.created_at).toLocaleTimeString("vi-VN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        day: "2-digit",
                        month: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
