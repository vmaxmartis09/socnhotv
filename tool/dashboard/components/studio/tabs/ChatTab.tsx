"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { useStudioStore } from "@/store";
import {
  sendChatToCore,
  FALLBACK_NODE_TYPES,
  estimateNodeCostUsd,
} from "@/lib/core-api";
import { PORT_TYPE_COLORS } from "@/store/slices/canvasSlice";
import { Send, Undo2, Copy, Trash2, Layers, Users, Bot, FolderGit2, Check } from "@/components/ui/icons";
import { getRepository } from "@/lib/repositories";
import { generateCharacterDraft } from "@/lib/repositories/character-assets";
import type { ChatModel } from "@/store/slices/chatSlice";
import { runLocalAgent } from "@/lib/studio-agent";
import { AiLoading } from "@/components/ui/AiLoading";
import { useRouter } from "@/i18n/routing";

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
    projects,
    characters,
    setCharacters,
    episodes,
    activeEpisodeId,
    selectEpisode,
    createEpisode,
    switchProject,
    chatContext,
    setChatContext,
    clearProjectChat,
    addJob,
  } = useStudioStore();

  const router = useRouter();
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [projectNew, setProjectNew] = useState(false);
  const [menu, setMenu] = useState<null | "slash" | "mention">(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const messages = chatByProject[activeProjectId] || [];
  const activeChar = characters.find((ch) => ch.id === chatContext.characterId) || null;
  const activeEpisode = episodes.find((e) => e.id === activeEpisodeId);

  const SLASH = [
    { cmd: "/flow", hint: locale === "vi" ? "Tạo flow mới từ mẫu theo ý tưởng" : "New flow from template + idea" },
    { cmd: "/blank", hint: locale === "vi" ? "Tạo flow trắng tinh" : "Create an empty flow" },
    { cmd: "/char", hint: locale === "vi" ? "Tạo nhân vật mới từ mô tả" : "Create a character from description" },
    { cmd: "/run", hint: locale === "vi" ? "Chạy flow hiện tại (tạo job)" : "Run current flow (creates a job)" },
    { cmd: "/clear", hint: locale === "vi" ? "Xóa hội thoại" : "Clear chat" },
  ];

  // Tự cuộn xuống cuối & co giãn ô nhập
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length, sending]);
  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }, [input]);

  const onInputChange = (v: string) => {
    setInput(v);
    if (/^\/\S*$/.test(v)) setMenu("slash");
    else if (/(^|\s)@\S*$/.test(v)) setMenu("mention");
    else setMenu(null);
  };

  const say = (text: string) =>
    addChatMessage(activeProjectId, {
      id: `msg_a_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 4)}`,
      role: "assistant",
      text,
      timestamp: new Date().toISOString(),
      mode: "provider",
    });

  const startRunConfirmation = (promptText: string) => {
    const estCost = nodes.reduce(
      (acc, n) => acc + estimateNodeCostUsd(n.data.nodeType, n.data.params || {}, isMockMode),
      0
    );
    setPendingConfirmation({
      id: `conf_${Date.now().toString(36)}`,
      kind: "run",
      titleVi: `Chạy flow “${activeEpisode?.title || "hiện tại"}”`,
      titleEn: `Run flow “${activeEpisode?.title || "current"}”`,
      detailVi: `Sẽ tạo 1 job. Chi phí ước tính: $${estCost.toFixed(2)} (${isMockMode ? "chạy thử $0" : "API thật"}).`,
      detailEn: `Creates 1 job. Estimated cost: $${estCost.toFixed(2)} (${isMockMode ? "mock $0" : "real API"}).`,
      estimatedCostUsd: estCost,
      mode: "all",
      prompt: promptText,
    });
  };

  /** Lệnh theo ngữ cảnh chọn trên thanh: flow mới/trắng, nhân vật tạo/cập nhật. Trả null nếu không áp dụng. */
  const runContextAction = async (text: string): Promise<string | null> => {
    const slash = /^\/(flow|blank|char|run|clear)\b\s*(.*)$/i.exec(text);
    const cmd = slash?.[1]?.toLowerCase();
    const body = (slash ? slash[2] : text).trim();

    if (cmd === "clear") { clearProjectChat(activeProjectId); return ""; }
    if (cmd === "run") { startRunConfirmation(text); return "Đang chờ bạn xác nhận chạy flow."; }

    const fl = chatContext.focus === "flow";
    const wantBlank = cmd === "blank" || (!cmd && fl && chatContext.flowMode === "blank");
    const wantFlow = cmd === "flow" || (!cmd && fl && chatContext.flowMode === "new");
    if (wantBlank || wantFlow) {
      const title = body.slice(0, 60) || (wantBlank ? "Flow trắng" : "Flow mới");
      const ep = createEpisode(title, { blank: wantBlank });
      if (wantFlow && body) {
        const st = useStudioStore.getState();
        st.setNodesAndEdges(
          st.nodes.map((n) => n.data.nodeType === "text" ? { ...n, data: { ...n.data, params: { ...n.data.params, content: body } } } : n),
          st.edges,
          false
        );
      }
      setChatContext({ flowMode: "current" });
      return wantBlank
        ? `Đã tạo flow trắng “${ep.title}” trong dự án ${activeProjectId}. Hãy nhờ tôi thêm node, hoặc kéo từ thư viện.`
        : `Đã tạo flow “${ep.title}” từ mẫu${body ? " và nạp ý tưởng vào node Text" : ""}. Bấm /run để chạy thành job.`;
    }

    const cf = chatContext.focus === "character";
    if (cmd === "char" || (!cmd && cf && chatContext.characterId === "__new__")) {
      if (!body) return "Hãy mô tả nhân vật, ví dụ: “bác sĩ cú mèo 140cm, hiền và thông minh”.";
      const { draft } = await generateCharacterDraft(activeProjectId, body, isMockMode);
      const id = draft.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || `char_${Date.now().toString(36)}`;
      await getRepository().createCharacter({
        id, projectId: activeProjectId, name: draft.name, role: draft.role, heightCm: draft.heightCm,
        scaleRatio: Math.round(draft.heightCm) / 100, voiceId: "", description: draft.description,
        promptLock: draft.promptLock, referenceImages: [],
        memory: { personality: draft.personality, catchphrases: draft.catchphrases ?? [], habits: draft.habits ?? [], pastEventsSummary: [] },
      } as any);
      setCharacters(await getRepository().listCharacters(activeProjectId));
      setChatContext({ characterId: id, characterMode: "update" });
      return `Đã tạo nhân vật “${draft.name}” (${draft.heightCm} cm) và chọn làm ngữ cảnh để bạn tiếp tục chỉnh.`;
    }

    if (!cmd && cf && activeChar && chatContext.characterMode === "update") {
      const { draft, mode } = await generateCharacterDraft(activeProjectId, `${activeChar.name}: ${activeChar.description || ""}. Cập nhật: ${body}`, isMockMode);
      // Bản nháp theo quy tắc chỉ chép lại câu lệnh nên không dùng làm mô tả/prompt lock; chỉ Gemini mới được ghi đè.
      // Chiều cao & promptLock luôn giữ theo khóa tỉ lệ.
      const updated = {
        ...activeChar,
        description: mode === "gemini" && draft.description ? draft.description : activeChar.description,
        memory: {
          ...activeChar.memory,
          personality: mode === "gemini" && draft.personality ? draft.personality : activeChar.memory?.personality,
          habits: mode === "gemini" ? draft.habits ?? activeChar.memory?.habits ?? [] : [...(activeChar.memory?.habits ?? []), body],
          catchphrases: mode === "gemini" ? draft.catchphrases ?? activeChar.memory?.catchphrases ?? [] : activeChar.memory?.catchphrases ?? [],
        },
      };
      await getRepository().upsertCharacter(activeProjectId, updated as any);
      setCharacters(await getRepository().listCharacters(activeProjectId));
      return `Đã cập nhật “${activeChar.name}” (${mode === "gemini" ? "Gemini" : "ghi vào thói quen/bộ nhớ, chưa có Gemini"}). Chiều cao ${activeChar.heightCm} cm giữ nguyên (khóa tỉ lệ).`;
    }
    if (!cmd && chatContext.focus === "project" && projectNew) {
      const r = await runLocalAgent(`tạo dự án ${body}`, { push: (path) => router.push(path) });
      setProjectNew(false);
      return r ?? "Đã xử lý.";
    }
    return null;
  };


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
          type: "default",
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
      try {
        const ctxReply = await runContextAction(promptText);
        if (ctxReply !== null) {
          if (ctxReply) say(ctxReply);
          setSending(false);
          return;
        }
      } catch (ctxErr) {
        say(`Không thực hiện được: ${ctxErr instanceof Error ? ctxErr.message : String(ctxErr)}`);
        setSending(false);
        return;
      }
      // Trợ lý cục bộ: tạo/kiểm tra mọi thứ trong dự án; không khớp thì chuyển cho Core/Gemini
      try {
        const local = await runLocalAgent(promptText, { push: (path) => router.push(path) });
        if (local !== null) {
          addChatMessage(activeProjectId, {
            id: `msg_a_${Date.now().toString(36)}`,
            role: "assistant",
            text: local,
            timestamp: new Date().toISOString(),
            mode: "provider",
          });
          setSending(false);
          return;
        }
      } catch (agentErr) {
        addChatMessage(activeProjectId, {
          id: `msg_a_${Date.now().toString(36)}`,
          role: "assistant",
          text: `Không thực hiện được: ${agentErr instanceof Error ? agentErr.message : String(agentErr)}`,
          timestamp: new Date().toISOString(),
          mode: "provider",
        });
        setSending(false);
        return;
      }
      const res = await sendChatToCore(activeProjectId, promptText, {
        model: chatContext.model,
        flow: activeEpisodeId,
        characterId: chatContext.characterId,
        characterMode: chatContext.characterMode,
      });
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
      addJob({
        id: `job_${Date.now().toString(36)}`,
        projectId: activeProjectId,
        type: "render",
        model: chatContext.model,
        status: "completed",
        progress: 100,
        estimatedCostUsd: pendingConfirmation.estimatedCostUsd || 0,
        actualCostUsd: isMockMode ? 0 : pendingConfirmation.estimatedCostUsd || 0,
        logs: [`Flow: ${activeEpisode?.title || activeEpisodeId}`, `Từ trợ lý Chat`],
        createdAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      });
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

  const vi = locale === "vi";
  const quickPrompts = useMemo(() => {
    const out: string[] = [];
    if (nodes.length === 0) out.push(vi ? "/flow Sóc Nhỏ đi tìm kho báu" : "/flow Squirrel treasure hunt");
    else out.push(vi ? "/run" : "/run");
    if (activeChar) out.push(vi ? `Làm ${activeChar.name} hiền hơn, thêm câu cửa miệng` : `Make ${activeChar.name} gentler`);
    else out.push(vi ? "/char bác sĩ cú mèo 140cm, hiền" : "/char owl doctor 140cm, gentle");
    out.push(t("quickPrompts.addGate"), t("quickPrompts.ratio169"), t("quickPrompts.scheduleYt"));
    return out;
  }, [nodes.length, activeChar, vi, t]);

  const sel = "h-7 min-w-0 flex-1 truncate rounded-md border border-border bg-card px-1.5 text-[12px] text-foreground";
  const lbl = "mb-0.5 flex items-center gap-1 text-[11px] font-medium text-muted-foreground";
  const mentionQ = /(?:^|\s)@(\S*)$/.exec(input)?.[1]?.toLowerCase() ?? "";
  const mentionList = characters.filter((ch) => ch.name.toLowerCase().includes(mentionQ));

  return (
    <div className="flex h-full flex-col text-xs">
      {/* Trọng tâm chat: Dự án / Nhân vật / Flow */}
      <div className="space-y-2 border-b border-border p-2.5">
        <div className="flex items-center gap-1.5">
          <div role="tablist" className="flex flex-1 rounded-lg bg-muted p-0.5">
            {([
              ["character", vi ? "Nhân vật" : "Character", Users],
              ["flow", "Flow", Layers],
              ["project", vi ? "Dự án" : "Project", FolderGit2],
            ] as const).map(([k, label, Icon]) => (
              <button
                key={k}
                type="button"
                role="tab"
                aria-selected={chatContext.focus === k}
                onClick={() => setChatContext({ focus: k })}
                className={`flex h-7 flex-1 items-center justify-center gap-1 rounded-md text-[12px] font-medium transition-colors ${
                  chatContext.focus === k ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-3 w-3" />{label}
              </button>
            ))}
          </div>
          <select aria-label="Model" className={sel + " !flex-none w-[92px]"} value={chatContext.model} onChange={(e) => setChatContext({ model: e.target.value as ChatModel })}>
            <option value="auto">Auto</option>
            <option value="gemini-2.5-pro">Gemini Pro</option>
            <option value="gemini-2.5-flash">Gemini Flash</option>
            <option value="rules">{vi ? "Quy tắc" : "Rules"}</option>
          </select>
        </div>

        <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <FolderGit2 className="h-3 w-3" />
          <select aria-label="Project" className="max-w-[140px] truncate bg-transparent font-medium text-foreground outline-none" value={activeProjectId} onChange={(e) => switchProject(e.target.value)}>
            {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          {vi ? "· mọi thao tác nằm trong dự án này" : "· all actions stay in this project"}
        </p>

        {chatContext.focus === "character" && (
          <div className="space-y-1">
            <div className="flex flex-wrap gap-1">
              <button type="button" onClick={() => setChatContext({ characterId: "__new__", characterMode: "create" })}
                className={`rounded-full border px-2 py-0.5 text-[12px] ${chatContext.characterId === "__new__" ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-accent"}`}>
                ＋ {vi ? "Tạo mới" : "New"}
              </button>
              {characters.map((ch) => (
                <button key={ch.id} type="button" onClick={() => setChatContext({ characterId: ch.id, characterMode: "update" })}
                  className={`rounded-full border px-2 py-0.5 text-[12px] ${chatContext.characterId === ch.id ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-accent"}`}>
                  {ch.name}
                </button>
              ))}
            </div>
            <p className="rounded-md bg-accent/60 px-2 py-1 text-[12px] text-foreground">
              {chatContext.characterId === "__new__"
                ? (vi ? "Mô tả nhân vật mới, AI dựng hồ sơ & lưu vào dự án." : "Describe a new character; AI builds & saves it.")
                : activeChar
                ? (vi ? `Đang cập nhật “${activeChar.name}” (${activeChar.heightCm} cm, khóa tỉ lệ). Nói điều muốn đổi.` : `Updating “${activeChar.name}”. Say what to change.`)
                : (vi ? "Chọn một nhân vật để cập nhật, hoặc ＋ Tạo mới." : "Pick a character to update, or ＋ New.")}
            </p>
          </div>
        )}

        {chatContext.focus === "flow" && (
          <div className="space-y-1">
            <div className="flex gap-1">
              <select aria-label="Flow" className={sel} value={activeEpisodeId} onChange={(e) => { setChatContext({ flowMode: "current" }); selectEpisode(e.target.value); }}>
                {episodes.map((ep) => <option key={ep.id} value={ep.id}>{ep.title}</option>)}
              </select>
              <button type="button" onClick={() => setChatContext({ flowMode: "blank" })} className={`shrink-0 rounded-md border px-2 text-[12px] ${chatContext.flowMode === "blank" ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-accent"}`}>＋ {vi ? "Trắng" : "Blank"}</button>
              <button type="button" onClick={() => setChatContext({ flowMode: "new" })} className={`shrink-0 rounded-md border px-2 text-[12px] ${chatContext.flowMode === "new" ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-accent"}`}>＋ {vi ? "Từ mẫu" : "Template"}</button>
            </div>
            <p className="rounded-md bg-accent/60 px-2 py-1 text-[12px] text-foreground">
              {chatContext.flowMode === "blank" ? (vi ? "Tin kế tiếp = tên flow trắng mới." : "Next message = new blank flow name.")
                : chatContext.flowMode === "new" ? (vi ? "Tin kế tiếp = ý tưởng, tạo flow từ mẫu 9 bước." : "Next message = idea for a template flow.")
                : (vi ? `Chat chỉnh flow “${activeEpisode?.title ?? ""}”: thêm node, đổi tỉ lệ, /run để chạy thành job.` : `Chat edits “${activeEpisode?.title ?? ""}”; /run creates a job.`)}
            </p>
          </div>
        )}

        {chatContext.focus === "project" && (
          <div className="space-y-1">
            <button type="button" onClick={() => setProjectNew((v) => !v)} className={`rounded-full border px-2 py-0.5 text-[12px] ${projectNew ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-accent"}`}>＋ {vi ? "Dự án mới" : "New project"}</button>
            <p className="rounded-md bg-accent/60 px-2 py-1 text-[12px] text-foreground">
              {projectNew ? (vi ? "Tin kế tiếp = tên dự án mới." : "Next message = new project name.")
                : (vi ? "Hỏi/ra lệnh ở cấp dự án: tạo tập, nhân vật, lên lịch đăng, mở trang…" : "Project-level commands: episodes, characters, schedule, navigation…")}
            </p>
          </div>
        )}
      </div>

      {/* Hội thoại */}
      <div className="scroll-quiet flex-1 space-y-2.5 overflow-y-auto p-3.5">
        {messages.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-3 text-muted-foreground">
            <p className="font-medium text-foreground">{t("assistantTitle")}</p>
            <p className="mt-0.5 leading-snug">{t("assistantSub")}</p>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={
              m.role === "user"
                ? "group ml-6 rounded-lg border border-border bg-accent/60 p-2.5 text-foreground"
                : "group mr-2 space-y-2 rounded-lg border border-border bg-card p-2.5 text-foreground"
            }
          >
            <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
            <button
              type="button"
              aria-label="Copy"
              onClick={() => { navigator.clipboard?.writeText(m.text); setCopiedId(m.id); setTimeout(() => setCopiedId(null), 1200); }}
              className="hidden h-5 items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground group-hover:inline-flex"
            >
              {copiedId === m.id ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copiedId === m.id ? (vi ? "Đã chép" : "Copied") : (vi ? "Chép" : "Copy")}
            </button>

            {m.actionCard && (
              <div className="space-y-1.5 rounded-md border border-border bg-muted/40 p-2">
                <p className="text-[13px] font-medium text-foreground">
                  {vi ? m.actionCard.summaryVi : m.actionCard.summaryEn}
                </p>
                <div className="flex items-center gap-1.5">
                  {m.actionCard.undone ? (
                    <span className="rounded bg-accent px-1.5 py-0.5 text-xs text-muted-foreground">{t("undoneBadge")}</span>
                  ) : (
                    m.actionCard.snapshotBefore && (
                      <button
                        type="button"
                        onClick={() => handleUndoChatAction(m.id, m.actionCard?.snapshotBefore)}
                        className="inline-flex h-6 items-center gap-1 rounded border border-border bg-card px-2 text-xs font-medium text-foreground hover:bg-accent"
                      >
                        <Undo2 className="h-2.5 w-2.5" />
                        <span>{t("undoActionBtn")}</span>
                      </button>
                    )
                  )}
                  {m.actionCard.targetNodeId && (
                    <button
                      type="button"
                      onClick={() => { setSelectedNodeId(m.actionCard!.targetNodeId!); flashNode(m.actionCard!.targetNodeId!); }}
                      className="inline-flex h-6 items-center rounded border border-border bg-card px-2 text-xs font-medium text-foreground hover:bg-accent"
                    >
                      {t("viewOnCanvasBtn")}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="mr-2 rounded-lg border border-border bg-card p-2.5">
            <AiLoading lines={2} />
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Gợi ý động + ô nhập */}
      <div className="border-t border-border p-2.5">
        <div className="scroll-quiet mb-2 flex gap-1.5 overflow-x-auto pb-0.5">
          {quickPrompts.map((qp) => (
            <button
              key={qp}
              type="button"
              disabled={sending}
              onClick={() => handleSendCommand(qp)}
              className="shrink-0 rounded-full border border-border bg-card px-2.5 py-1 text-[12px] text-foreground hover:bg-accent disabled:opacity-50"
            >
              {qp}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); setMenu(null); handleSendCommand(); }}
          className="relative"
        >
          {menu && (
            <ul className="absolute bottom-full left-0 right-0 mb-1 max-h-40 overflow-y-auto rounded-md border border-border bg-popover p-1 shadow-md">
              {menu === "slash" &&
                SLASH.filter((x) => x.cmd.startsWith(input.trim())).map((x) => (
                  <li key={x.cmd}>
                    <button type="button" onClick={() => { setInput(x.cmd + " "); setMenu(null); taRef.current?.focus(); }} className="flex w-full items-center gap-2 rounded px-2 py-1 text-left hover:bg-accent">
                      <code className="font-semibold">{x.cmd}</code><span className="text-muted-foreground">{x.hint}</span>
                    </button>
                  </li>
                ))}
              {menu === "mention" &&
                (mentionList.length ? mentionList : []).map((ch) => (
                  <li key={ch.id}>
                    <button type="button" onClick={() => { setInput(input.replace(/@\S*$/, `@${ch.name} `)); setChatContext({ characterId: ch.id, characterMode: "update" }); setMenu(null); taRef.current?.focus(); }} className="flex w-full items-center gap-2 rounded px-2 py-1 text-left hover:bg-accent">
                      <Users className="h-3 w-3" /><span>{ch.name}</span><span className="text-muted-foreground">{ch.heightCm} cm</span>
                    </button>
                  </li>
                ))}
            </ul>
          )}
          <div className="flex items-end gap-1.5 rounded-lg border border-border bg-card p-1.5 focus-within:ring-1 focus-within:ring-ring">
            <textarea
              ref={taRef}
              rows={1}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); setMenu(null); handleSendCommand(); }
                if (e.key === "Escape") setMenu(null);
              }}
              placeholder={vi ? "Nhắn…  / lệnh · @ nhân vật · Shift+Enter xuống dòng" : "Message…  / commands · @ character · Shift+Enter newline"}
              className="max-h-[140px] min-h-[28px] flex-1 resize-none bg-transparent px-1.5 py-1 text-xs text-foreground outline-none"
            />
            <button
              type="button"
              aria-label="Clear"
              onClick={() => clearProjectChat(activeProjectId)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="flex h-7 items-center gap-1 rounded-md bg-primary px-2.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
            >
              <Send className="h-3.5 w-3.5" />
              <span>{t("sendBtn")}</span>
            </button>
          </div>
        </form>
      </div>

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
