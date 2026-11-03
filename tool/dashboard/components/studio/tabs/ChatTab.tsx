"use client";

import React, { useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useStudioStore } from "@/store";
import {
  sendChatToCore,
  FALLBACK_NODE_TYPES,
  estimateNodeCostUsd,
} from "@/lib/core-api";
import { PORT_TYPE_COLORS } from "@/store/slices/canvasSlice";
import { Send, Undo2 } from "@/components/ui/icons";

export function ChatTab() {
  const t = useTranslations("chatTab");
  const c = useTranslations("common");
  const locale = useLocale() as "vi" | "en";

  const {
    activeProjectId,
    chatByProject,
    addChatMessage,
    markChatActionUndone,
    pendingConfirmation,
    setPendingConfirmation,
    nodes,
    edges,
    aspectRatio,
    setAspectRatio,
    setNodesAndEdges,
    setSelectedNodeId,
    flashNode,
    setActiveRightTab,
    setSelectedCharacterId,
    setActiveCharacterSection,
    addScheduledPost,
    isMockMode,
    updateNodeExecutionState,
  } = useStudioStore();

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const messages = chatByProject[activeProjectId] || [];

  const executeStudioAction = (action: any): { targetNodeId?: string } => {
    if (!action) return {};

    if (action.type === "add_node") {
      const nodeType = action.nodeType || "quality_check";
      const def =
        FALLBACK_NODE_TYPES.find((d) => d.typeName === nodeType) ||
        FALLBACK_NODE_TYPES[0];
      const newId = `node_${nodeType}_${Date.now().toString(36).slice(-3)}`;

      // Find anchor node (e.g. image_gen)
      const afterNode =
        nodes.find((n) => n.data.nodeType === (action.afterNodeType || "image_gen")) ||
        nodes[nodes.length - 1];
      const pos = afterNode
        ? { x: afterNode.position.x + 170, y: afterNode.position.y + 120 }
        : { x: 600, y: 200 };

      const newNode = {
        id: newId,
        type: "studioCard",
        position: pos,
        selected: true,
        data: {
          nodeType: def.typeName,
          status: "idle" as const,
          params: { ...(def.defaultParams || {}) },
          generations: [],
          nextStepHint: "Được thêm từ trợ lý Chat",
        },
      };

      const nextEdges = [...edges];
      if (afterNode && def.inputPorts.length > 0) {
        nextEdges.push({
          id: `e_chat_${Date.now().toString(36)}`,
          source: afterNode.id,
          sourceHandle:
            afterNode.data.nodeType === "image_gen" ? "image" : "text",
          target: newId,
          targetHandle: def.inputPorts[0].name,
          type: "smoothstep",
          style: {
            stroke:
              PORT_TYPE_COLORS[def.inputPorts[0].portType] || "#1b6c80",
            strokeWidth: 1.75,
          },
        });
      }

      setNodesAndEdges(
        [...nodes.map((n) => ({ ...n, selected: false })), newNode],
        nextEdges,
        true
      );
      setSelectedNodeId(newId);
      flashNode(newId);
      return { targetNodeId: newId };
    }

    if (action.type === "set_aspect_ratio" && action.aspectRatio) {
      setAspectRatio(action.aspectRatio);
      const firstGen = nodes.find(
        (n) =>
          n.data.nodeType === "image_gen" || n.data.nodeType === "video_gen"
      );
      if (firstGen) flashNode(firstGen.id);
      return { targetNodeId: firstGen?.id };
    }

    if (action.type === "open_tab" && action.tab) {
      setActiveRightTab(action.tab);
      return {};
    }

    if (action.type === "open_character") {
      setActiveRightTab("project");
      setSelectedCharacterId(action.characterId || "koala");
      setActiveCharacterSection("profile");
      const charNode = nodes.find((n) => n.data.nodeType === "character");
      if (charNode) flashNode(charNode.id);
      return { targetNodeId: charNode?.id };
    }

    return {};
  };

  const handleSendCommand = async (rawPrompt?: string) => {
    const promptText = (rawPrompt ?? input).trim();
    if (!promptText || sending) return;
    if (!rawPrompt) setInput("");
    setSending(true);

    const userMsgId = `msg_u_${Date.now().toString(36)}`;
    addChatMessage(activeProjectId, {
      id: userMsgId,
      role: "user",
      text: promptText,
      timestamp: new Date().toISOString(),
    });

    const snapshotBefore = {
      nodes: [...nodes],
      edges: [...edges],
      aspectRatio,
    };

    try {
      const res = await sendChatToCore(activeProjectId, promptText);
      const firstAction = res.actions?.[0];

      // If requiresConfirmation (paid run or external publish), open confirmation dialog first!
      if (res.requiresConfirmation && res.confirmationMeta) {
        const meta = res.confirmationMeta;
        const estCost = nodes.reduce(
          (acc, n) =>
            acc +
            estimateNodeCostUsd(
              n.data.nodeType,
              n.data.params || {},
              isMockMode
            ),
          0
        );
        setPendingConfirmation({
          id: `conf_${Date.now().toString(36)}`,
          kind: meta.kind === "publish" ? "publish" : "run",
          titleVi:
            meta.kind === "publish"
              ? `Xác nhận lên lịch đăng lên ${(meta.platform || "youtube").toUpperCase()}`
              : "Xác nhận chạy đồ thị từ trợ lý Chat",
          titleEn:
            meta.kind === "publish"
              ? `Confirm scheduling on ${(meta.platform || "youtube").toUpperCase()}`
              : "Confirm running graph from Chat assistant",
          detailVi:
            meta.kind === "publish"
              ? `Bài đăng: "${meta.episodeTitle || "Tập 1"}" lúc ${
                  meta.time || "19:00"
                } trên nền tảng ${(meta.platform || "youtube").toUpperCase()}.`
              : `Chế độ chạy: ${
                  meta.mode || "all"
                }. Chi phí ước tính: $${estCost.toFixed(2)} USD (${
                  isMockMode ? "Chế độ chạy thử $0" : "API thật"
                }).`,
          detailEn:
            meta.kind === "publish"
              ? `Post: "${meta.episodeTitle || "Episode 1"}" at ${
                  meta.time || "19:00"
                } on ${(meta.platform || "youtube").toUpperCase()}.`
              : `Run mode: ${
                  meta.mode || "all"
                }. Estimated cost: $${estCost.toFixed(2)} USD.`,
          estimatedCostUsd: estCost,
          platform: meta.platform,
          time: meta.time,
          episodeTitle: meta.episodeTitle,
          mode: meta.mode,
          prompt: promptText,
        });

        addChatMessage(activeProjectId, {
          id: `msg_a_${Date.now().toString(36)}`,
          role: "assistant",
          text: res.reply,
          timestamp: new Date().toISOString(),
          mode: (res.mode as any) || "rule_based_mock",
          actionCard: firstAction
            ? {
                id: `act_${Date.now().toString(36)}`,
                summaryVi: firstAction.summaryVi || "Đang chờ xác nhận...",
                summaryEn: firstAction.summaryEn || "Awaiting confirmation...",
                snapshotBefore,
              }
            : undefined,
        });
        return;
      }

      // Immediate non-destructive studio action
      const { targetNodeId } = executeStudioAction(firstAction);

      addChatMessage(activeProjectId, {
        id: `msg_a_${Date.now().toString(36)}`,
        role: "assistant",
        text: res.reply,
        timestamp: new Date().toISOString(),
        mode: (res.mode as any) || "rule_based_mock",
        actionCard: firstAction
          ? {
              id: `act_${Date.now().toString(36)}`,
              summaryVi:
                firstAction.summaryVi || "Đã thực hiện thao tác trên Studio",
              summaryEn:
                firstAction.summaryEn || "Executed action on Studio canvas",
              targetNodeId,
              snapshotBefore,
            }
          : undefined,
      });
    } finally {
      setSending(false);
    }
  };

  const handleConfirmPendingAction = () => {
    if (!pendingConfirmation) return;
    if (pendingConfirmation.kind === "publish") {
      addScheduledPost({
        id: `sched_${Date.now().toString(36)}`,
        projectId: activeProjectId,
        episodeId: "ep_01_rang_sau",
        episodeTitle:
          pendingConfirmation.episodeTitle ||
          "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
        channelId: `ch_${pendingConfirmation.platform || "youtube"}`,
        channelName: `${(
          pendingConfirmation.platform || "youtube"
        ).toUpperCase()} Sóc Nhỏ TV`,
        platform: (pendingConfirmation.platform as any) || "youtube",
        scheduledAt: `Hàng ngày · ${pendingConfirmation.time || "19:00"}`,
        status: "pending_approval",
        manualApprovalRequired: true,
      });
      setActiveRightTab("publish");
    } else {
      for (const n of nodes) {
        updateNodeExecutionState(n.id, {
          status: "succeeded",
          isStale: false,
        });
      }
      if (nodes[0]) flashNode(nodes[0].id);
    }
    setPendingConfirmation(null);
  };

  const handleUndoChatAction = (msgId: string, snapshot?: any) => {
    if (!snapshot) return;
    setNodesAndEdges(snapshot.nodes, snapshot.edges, false);
    if (snapshot.aspectRatio) {
      setAspectRatio(snapshot.aspectRatio);
    }
    markChatActionUndone(activeProjectId, msgId);
  };

  const quickPrompts = [
    t("quickPrompts.addGate"),
    t("quickPrompts.ratio169"),
    t("quickPrompts.runScene3"),
    t("quickPrompts.scheduleYt"),
    t("quickPrompts.openSchedule"),
    t("quickPrompts.viewKoala"),
  ];

  return (
    <div className="flex h-full flex-col justify-between p-3.5 text-xs">
      {/* Header + Quick Command Chips */}
      <div className="space-y-3 overflow-y-auto pr-0.5">
        <div className="border-b border-border pb-2.5">
          <h3 className="text-sm font-semibold text-foreground">
            {t("assistantTitle")}
          </h3>
          <p className="mt-0.5 text-[11px] text-muted-foreground leading-snug">
            {t("assistantSub")}
          </p>
        </div>

        {/* Quick prompts */}
        <div className="flex flex-wrap gap-1.5">
          {quickPrompts.map((qp) => (
            <button
              key={qp}
              type="button"
              onClick={() => handleSendCommand(qp)}
              className="rounded-md border border-border bg-card px-2 py-1 text-left text-[11px] text-foreground hover:bg-accent"
            >
              {qp}
            </button>
          ))}
        </div>

        {/* Conversation history */}
        <div className="space-y-2.5 pt-1">
          {messages.map((m) => (
            <div
              key={m.id}
              className={
                m.role === "user"
                  ? "ml-6 rounded-lg border border-border bg-accent/60 p-2.5 text-foreground"
                  : "mr-2 rounded-lg border border-border bg-card p-2.5 text-foreground space-y-2"
              }
            >
              <p className="leading-relaxed">{m.text}</p>

              {/* Compact Action Card with Undo & View on Canvas */}
              {m.actionCard && (
                <div className="rounded-md border border-border bg-muted/40 p-2 space-y-1.5">
                  <p className="text-[11px] font-medium text-foreground">
                    {locale === "vi"
                      ? m.actionCard.summaryVi
                      : m.actionCard.summaryEn}
                  </p>
                  <div className="flex items-center gap-1.5">
                    {m.actionCard.undone ? (
                      <span className="rounded bg-accent px-1.5 py-0.5 text-[10px] text-muted-foreground">
                        {t("undoneBadge")}
                      </span>
                    ) : (
                      m.actionCard.snapshotBefore && (
                        <button
                          type="button"
                          onClick={() =>
                            handleUndoChatAction(
                              m.id,
                              m.actionCard?.snapshotBefore
                            )
                          }
                          className="inline-flex h-6 items-center gap-1 rounded border border-border bg-card px-2 text-[10px] font-medium text-foreground hover:bg-accent"
                        >
                          <Undo2 className="h-2.5 w-2.5" />
                          <span>{t("undoActionBtn")}</span>
                        </button>
                      )
                    )}

                    {m.actionCard.targetNodeId && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedNodeId(m.actionCard!.targetNodeId!);
                          flashNode(m.actionCard!.targetNodeId!);
                        }}
                        className="inline-flex h-6 items-center rounded border border-border bg-card px-2 text-[10px] font-medium text-foreground hover:bg-accent"
                      >
                        {t("viewOnCanvasBtn")}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Chat Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendCommand();
        }}
        className="mt-3 flex items-center gap-1.5 border-t border-border pt-2.5"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("inputPlaceholder")}
          className="h-8 flex-1 rounded-md border border-border bg-card px-2.5 text-xs text-foreground"
        />
        <button
          type="submit"
          disabled={sending}
          className="flex h-8 items-center gap-1 rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground"
        >
          <Send className="h-3.5 w-3.5" />
          <span>{t("sendBtn")}</span>
        </button>
      </form>

      {/* Confirmation Modal for Paid Run or External Publishing */}
      {pendingConfirmation && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={t("confirmModalTitle")}
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/25 p-4"
        >
          <div className="w-full max-w-md rounded-lg border border-border bg-popover p-4 text-popover-foreground space-y-3">
            <h4 className="text-sm font-semibold">
              {locale === "vi"
                ? pendingConfirmation.titleVi
                : pendingConfirmation.titleEn}
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed tnum">
              {locale === "vi"
                ? pendingConfirmation.detailVi
                : pendingConfirmation.detailEn}
            </p>
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setPendingConfirmation(null)}
                className="h-8 rounded border border-border bg-card px-3 text-xs text-foreground"
              >
                {c("cancel")}
              </button>
              <button
                type="button"
                onClick={handleConfirmPendingAction}
                className="h-8 rounded bg-primary px-3 text-xs font-medium text-primary-foreground"
              >
                {t("confirmProceed")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
