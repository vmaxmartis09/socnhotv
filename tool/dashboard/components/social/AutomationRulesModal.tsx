"use client";

import React, { useState } from "react";
import { useSocialStore } from "@/store/modules/social";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Play,
  RefreshCw,
  Sparkles,
  X,
  Zap,
} from "./icons";

interface AutomationRulesModalProps {
  projectId: string;
}

export function AutomationRulesModal({ projectId }: AutomationRulesModalProps) {
  const {
    automationRules,
    isAutomationModalOpen,
    setAutomationModalOpen,
    toggleAutomationRule,
    runAutomation,
  } = useSocialStore();

  const [runningRuleId, setRunningRuleId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isAutomationModalOpen) return null;

  const handleRun = async (ruleId: string) => {
    setRunningRuleId(ruleId);
    setSuccessMsg(null);
    try {
      await runAutomation(projectId, ruleId);
      setSuccessMsg("Đã kích hoạt chạy thử quy tắc thành công!");
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (e: any) {
      alert("Lỗi khi chạy quy tắc: " + e.message);
    } finally {
      setRunningRuleId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={() => setAutomationModalOpen(false)}
        />

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white dark:bg-zinc-900 rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full border border-zinc-200 dark:border-zinc-800">
          {/* Header */}
          <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-zinc-900 dark:text-white">
                  Quy Tắc Tự Động Hoá (Automation Rules)
                </h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Tự động chuyển đổi sự kiện Render và Kịch bản sang bài viết và đặt lịch đăng
                </p>
              </div>
            </div>
            <button
              onClick={() => setAutomationModalOpen(false)}
              className="p-2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Feedback banner */}
          {successMsg && (
            <div className="mx-6 mt-4 p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center gap-2 text-sm text-emerald-800 dark:text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              {successMsg}
            </div>
          )}

          {/* Rules List */}
          <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
            {automationRules.length === 0 ? (
              <p className="text-center py-8 text-sm text-zinc-500">
                Chưa có quy tắc tự động nào được khởi tạo.
              </p>
            ) : (
              automationRules.map((rule) => {
                const autoApprove = rule.actions?.auto_approve === true;
                return (
                  <div
                    key={rule.id}
                    className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30 flex flex-col gap-3"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm text-zinc-900 dark:text-white">
                            {rule.name}
                          </h4>
                          <span
                            className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${
                              rule.trigger === "render_done"
                                ? "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/50 dark:text-cyan-300"
                                : rule.trigger === "schedule_gap"
                                ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300"
                                : "bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300"
                            }`}
                          >
                            {rule.trigger}
                          </span>
                        </div>

                        {/* Conditions and Actions summary */}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {rule.conditions?.template_id_prefix && (
                            <span className="text-xs bg-zinc-200/70 dark:bg-zinc-700/60 text-zinc-700 dark:text-zinc-300 px-2 py-0.5 rounded">
                              Mẫu: {rule.conditions.template_id_prefix}*
                            </span>
                          )}
                          {rule.actions?.platforms && (
                            <span className="text-xs bg-zinc-200/70 dark:bg-zinc-700/60 text-zinc-700 dark:text-zinc-300 px-2 py-0.5 rounded">
                              Nền tảng: {rule.actions.platforms.join(", ")}
                            </span>
                          )}
                          {rule.conditions?.min_weekly_posts && (
                            <span className="text-xs bg-zinc-200/70 dark:bg-zinc-700/60 text-zinc-700 dark:text-zinc-300 px-2 py-0.5 rounded">
                              Tối thiểu: {rule.conditions.min_weekly_posts} bài/tuần
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Switch */}
                      <button
                        onClick={() => toggleAutomationRule(projectId, rule.id)}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                          rule.enabled ? "bg-indigo-600" : "bg-zinc-300 dark:bg-zinc-700"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            rule.enabled ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>

                    {/* Safety Alert if Auto Approve */}
                    {autoApprove && (
                      <div className="p-2.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg flex items-center gap-2 text-xs text-rose-700 dark:text-rose-300">
                        <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        <span>
                          <strong>Cảnh báo:</strong> Quy tắc này được cấu hình tự động duyệt (Auto-Approve), video sẽ được xuất bản mà không cần con người phê duyệt trước.
                        </span>
                      </div>
                    )}

                    {/* Bottom Status & Test Run */}
                    <div className="pt-2 border-t border-zinc-200/60 dark:border-zinc-800/60 flex items-center justify-between text-xs text-zinc-500">
                      <div>
                        {rule.last_run_at ? (
                          <span>
                            Chạy lần cuối:{" "}
                            {new Date(rule.last_run_at).toLocaleTimeString("vi-VN", {
                              hour: "2-digit",
                              minute: "2-digit",
                              day: "2-digit",
                              month: "2-digit",
                            })}
                            {" "}({rule.run_count} lần)
                          </span>
                        ) : (
                          <span>Chưa chạy lần nào</span>
                        )}
                      </div>

                      <button
                        onClick={() => handleRun(rule.id)}
                        disabled={runningRuleId === rule.id}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-800 dark:text-zinc-200 font-medium transition"
                      >
                        {runningRuleId === rule.id ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Play className="w-3.5 h-3.5" />
                        )}
                        Chạy thử
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
