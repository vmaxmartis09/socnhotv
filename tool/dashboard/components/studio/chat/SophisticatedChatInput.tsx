"use client";
import { showAlert } from "@/lib/confirm";

import React, { useRef, useState, useEffect } from "react";
import { useTranslations, useLocale } from "next-intl";
import type { ChatModel } from "@/store/slices/chatSlice";
import {
  Plus,
  ArrowRight,
  Mic,
  ShieldCheck,
  ChevronUp,
  Sparkles,
  Users,
  Layers,
  Trash2,
  Check,
  Bot,
  Workflow,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

interface Props {
  input: string;
  onInputChange: (val: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  model: ChatModel;
  onModelChange: (m: ChatModel) => void;
  isMockMode: boolean;
  onToggleMockMode?: () => void;
  characters: { id: string; name: string; heightCm: number }[];
  onMentionSelect: (charId: string, charName: string) => void;
  onSlashSelect: (cmd: string) => void;
  onClearChat: () => void;
  slashCommands: { cmd: string; hint: string }[];
  placeholder?: string;
}

const MODEL_OPTIONS: { id: ChatModel; name: string; tag: string; desc: string }[] = [
  {
    id: "gemini-3.8-flash",
    name: "Gemini 3.8 Flash",
    tag: "High",
    desc: "Mô hình thế hệ mới: suy luận cực nhanh, thông minh và tối ưu chi phí",
  },
  {
    id: "gemini-2.5-pro",
    name: "Gemini 2.5 Pro",
    tag: "SOTA",
    desc: "Lập luận sâu, phân tích kịch bản phức tạp và sinh cấu trúc flow chuẩn xác",
  },
  {
    id: "gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    tag: "Fast",
    desc: "Cân bằng tốc độ cao và phản hồi tức thời cho các lệnh thông thường",
  },
  {
    id: "auto",
    name: "Auto Route",
    tag: "Smart",
    desc: "Tự động phân bổ mô hình phù hợp dựa trên độ phức tạp của yêu cầu",
  },
  {
    id: "rules",
    name: "Quy tắc Cục bộ",
    tag: "$0",
    desc: "Chạy thử không tốn API, điều khiển đồ thị và nhân vật theo mẫu",
  },
];

export function SophisticatedChatInput({
  input,
  onInputChange,
  onSubmit,
  disabled = false,
  model,
  onModelChange,
  isMockMode,
  onToggleMockMode,
  characters,
  onMentionSelect,
  onSlashSelect,
  onClearChat,
  slashCommands,
  placeholder,
}: Props) {
  const t = useTranslations("chatTab");
  const locale = useLocale();
  const isVi = locale === "vi";

  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [plusMenuOpen, setPlusMenuOpen] = useState(false);
  const [modeMenuOpen, setModeMenuOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Lấy nhãn hiển thị cho model hiện tại
  const currentModelObj = MODEL_OPTIONS.find((m) => m.id === model) || MODEL_OPTIONS[0];

  // Auto-resize textarea theo nội dung
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(Math.max(el.scrollHeight, 40), 140)}px`;
  }, [input]);

  // Đóng popovers khi click ra ngoài
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setModelMenuOpen(false);
        setPlusMenuOpen(false);
        setModeMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Nhận diện giọng nói (Web Speech API)
  const toggleSpeechRecognition = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showAlert("Ghi âm giọng nói", isVi ? "Trình duyệt chưa hỗ trợ ghi âm trực tiếp." : "Speech recognition not supported in this browser.", "warning");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = isVi ? "vi-VN" : "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => setIsListening(true);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          onInputChange(input ? `${input} ${transcript}` : transcript);
        }
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  // Phát hiện autocomplete /slash hoặc @mention
  const isSlash = /^\/\S*$/.test(input);
  const isMention = /(?:^|\s)@(\S*)$/.test(input);
  const mentionQuery = /(?:^|\s)@(\S*)$/.exec(input)?.[1]?.toLowerCase() ?? "";
  const filteredChars = characters.filter((c) => c.name.toLowerCase().includes(mentionQuery));

  const defaultPlaceholder = isVi
    ? "Hỏi bất cứ điều gì, @ để nhắc nhân vật, / cho thao tác..."
    : "Ask anything, @ to mention, / for actions";

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Autocomplete Menu: Slash Commands */}
      {isSlash && (
        <ul className="absolute bottom-full left-0 right-0 mb-2 max-h-48 overflow-y-auto rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95 z-20 scroll-quiet">
          {slashCommands
            .filter((x) => x.cmd.startsWith(input.trim()))
            .map((item) => (
              <li key={item.cmd}>
                <button
                  type="button"
                  onClick={() => {
                    onSlashSelect(item.cmd);
                    textareaRef.current?.focus();
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-xs hover:bg-accent transition-colors"
                >
                  <code className="rounded bg-muted px-1.5 py-0.5 font-semibold text-foreground">{item.cmd}</code>
                  <span className="text-muted-foreground">{item.hint}</span>
                </button>
              </li>
            ))}
        </ul>
      )}

      {/* Autocomplete Menu: @ Mentions */}
      {isMention && filteredChars.length > 0 && (
        <ul className="absolute bottom-full left-0 right-0 mb-2 max-h-48 overflow-y-auto rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95 z-20 scroll-quiet">
          {filteredChars.map((ch) => (
            <li key={ch.id}>
              <button
                type="button"
                onClick={() => {
                  onMentionSelect(ch.id, ch.name);
                  textareaRef.current?.focus();
                }}
                className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left text-xs hover:bg-accent transition-colors"
              >
                <Users className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="font-medium text-foreground">{ch.name}</span>
                <span className="ml-auto text-[11px] text-muted-foreground tnum">{ch.heightCm} cm</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Popover: Menu dấu + */}
      {plusMenuOpen && (
        <div className="absolute bottom-[calc(100%+8px)] left-2 w-64 rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95 z-30 space-y-0.5 text-xs">
          <button
            type="button"
            onClick={() => {
              onInputChange(input ? `${input} @` : "@");
              setPlusMenuOpen(false);
              textareaRef.current?.focus();
            }}
            className="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 hover:bg-accent transition-colors text-left"
          >
            <Users className="h-4 w-4 text-brand" />
            <div>
              <p className="font-medium text-foreground">{isVi ? "Nhắc nhân vật" : "Mention character"}</p>
              <p className="text-[11px] text-muted-foreground">{isVi ? "Gõ @ để khóa ngữ cảnh nhân vật" : "Type @ to focus on character"}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => {
              onInputChange("/flow ");
              setPlusMenuOpen(false);
              textareaRef.current?.focus();
            }}
            className="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 hover:bg-accent transition-colors text-left"
          >
            <Workflow className="h-4 w-4 text-brand" />
            <div>
              <p className="font-medium text-foreground">{isVi ? "Tạo flow mới" : "New workflow"}</p>
              <p className="text-[11px] text-muted-foreground">{isVi ? "/flow dựng kịch bản từ ý tưởng" : "/flow generates flow from idea"}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => {
              onInputChange("/char ");
              setPlusMenuOpen(false);
              textareaRef.current?.focus();
            }}
            className="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 hover:bg-accent transition-colors text-left"
          >
            <Sparkles className="h-4 w-4 text-brand" />
            <div>
              <p className="font-medium text-foreground">{isVi ? "Tạo nhân vật mới" : "New character"}</p>
              <p className="text-[11px] text-muted-foreground">{isVi ? "/char mô tả để AI dựng hồ sơ DNA" : "/char to draft character DNA"}</p>
            </div>
          </button>
          <div className="my-1 border-t border-border/60" />
          <button
            type="button"
            onClick={() => {
              onClearChat();
              setPlusMenuOpen(false);
            }}
            className="flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-semantic-danger hover:bg-semantic-danger/10 transition-colors text-left"
          >
            <Trash2 className="h-4 w-4" />
            <span className="font-medium">{isVi ? "Xóa cuộc trò chuyện này" : "Clear conversation"}</span>
          </button>
        </div>
      )}

      {/* Popover: Menu chọn Model */}
      {modelMenuOpen && (
        <div className="absolute bottom-[calc(100%+8px)] left-8 w-72 rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95 z-30 space-y-1">
          <p className="px-2.5 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            {isVi ? "Mô hình ngôn ngữ" : "Language Model"}
          </p>
          {MODEL_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => {
                onModelChange(opt.id);
                setModelMenuOpen(false);
              }}
              className={cn(
                "flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2 text-left transition-colors",
                model === opt.id ? "bg-accent/80 text-foreground" : "hover:bg-accent/40 text-muted-foreground hover:text-foreground"
              )}
            >
              <Bot className="mt-0.5 h-4 w-4 text-brand shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-foreground">{opt.name}</span>
                  <span className="rounded-full bg-brand/10 px-1.5 py-0.2 text-[10px] font-medium text-brand">
                    {opt.tag}
                  </span>
                  {model === opt.id && <Check className="ml-auto h-3.5 w-3.5 text-brand" />}
                </div>
                <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground line-clamp-2">{opt.desc}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Popover: Menu chọn Mode Turbo / Chạy thử */}
      {modeMenuOpen && (
        <div className="absolute bottom-[calc(100%+8px)] right-12 w-64 rounded-2xl border border-border/80 bg-popover/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-0 zoom-in-95 z-30 space-y-1 text-xs">
          <p className="px-2.5 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            {isVi ? "Chế độ thực thi" : "Execution Mode"}
          </p>
          <button
            type="button"
            onClick={() => {
              if (isMockMode && onToggleMockMode) onToggleMockMode();
              setModeMenuOpen(false);
            }}
            className={cn(
              "flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2 text-left transition-colors",
              !isMockMode ? "bg-accent/80 text-foreground" : "hover:bg-accent/40 text-muted-foreground hover:text-foreground"
            )}
          >
            <ShieldCheck className="mt-0.5 h-4 w-4 text-brand shrink-0" />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-foreground">Turbo</span>
                <span className="rounded-full bg-brand/10 px-1.5 py-0.2 text-[10px] font-medium text-brand">
                  Live SOTA
                </span>
                {!isMockMode && <Check className="ml-auto h-3.5 w-3.5 text-brand" />}
              </div>
              <p className="text-[11px] text-muted-foreground">
                {isVi ? "Thực thi trực tiếp qua Gemini API" : "Live execution via Gemini API"}
              </p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => {
              if (!isMockMode && onToggleMockMode) onToggleMockMode();
              setModeMenuOpen(false);
            }}
            className={cn(
              "flex w-full items-start gap-2.5 rounded-xl px-2.5 py-2 text-left transition-colors",
              isMockMode ? "bg-accent/80 text-foreground" : "hover:bg-accent/40 text-muted-foreground hover:text-foreground"
            )}
          >
            <Bot className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-foreground">{isVi ? "Chạy thử ($0)" : "Mock ($0)"}</span>
                <span className="rounded-full bg-muted px-1.5 py-0.2 text-[10px] font-medium text-muted-foreground">
                  Free
                </span>
                {isMockMode && <Check className="ml-auto h-3.5 w-3.5 text-brand" />}
              </div>
              <p className="text-[11px] text-muted-foreground">
                {isVi ? "Chế độ mô phỏng không tốn chi phí" : "Zero-cost simulated responses"}
              </p>
            </div>
          </button>
        </div>
      )}

      {/* KHUNG CHAT BO TRÒN TINH TẾ (SOPHISTICATED CAPSULE INPUT) */}
      <div
        className={cn(
          "relative flex flex-col rounded-[26px] border border-border/80 bg-card/90 backdrop-blur-xl transition-all duration-200",
          "shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05),0_0_0_1px_rgba(0,0,0,0.02)]",
          "dark:bg-card/85 dark:border-white/10 dark:shadow-[0_8px_30px_rgba(0,0,0,0.35)]",
          "focus-within:border-foreground/30 focus-within:ring-2 focus-within:ring-brand/20 focus-within:shadow-[0_6px_28px_rgba(0,0,0,0.08)]"
        )}
      >
        {/* VÙNG NHẬP TEXT CHÍNH */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              setModelMenuOpen(false);
              setPlusMenuOpen(false);
              setModeMenuOpen(false);
              onSubmit();
            }
          }}
          placeholder={placeholder || defaultPlaceholder}
          className="w-full resize-none bg-transparent px-4 pt-3.5 pb-2 text-sm text-foreground placeholder:text-muted-foreground/60 outline-none leading-relaxed"
        />

        {/* THANH CÔNG CỤ PHÍA DƯỚI (BOTTOM TOOLBAR) */}
        <div className="flex items-center justify-between gap-2 px-3 pb-2.5 pt-0.5 select-none">
          {/* NHÓM ĐIỀU KHIỂN BÊN TRÁI: Nút '+' & Pill chọn Model */}
          <div className="flex items-center gap-1.5">
            {/* Nút '+' */}
            <button
              type="button"
              title={isVi ? "Thao tác nhanh" : "Actions"}
              aria-label={isVi ? "Thao tác nhanh" : "Actions"}
              onClick={() => {
                setPlusMenuOpen((v) => !v);
                setModelMenuOpen(false);
                setModeMenuOpen(false);
              }}
              className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground hover:bg-muted/70 hover:text-foreground active:scale-90 transition-colors"
            >
              <Plus className="h-4 w-4" />
            </button>

            {/* Pill Model: e.g. Gemini 3.8 Flash High ^ */}
            <button
              type="button"
              onClick={() => {
                setModelMenuOpen((v) => !v);
                setPlusMenuOpen(false);
                setModeMenuOpen(false);
              }}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-muted/30 px-2.5 py-1 text-xs font-medium text-foreground/80 hover:bg-muted/70 hover:text-foreground active:scale-95 transition-all cursor-pointer",
                modelMenuOpen && "border-brand/50 bg-muted text-foreground"
              )}
            >
              <span className="truncate max-w-[140px] sm:max-w-none">{currentModelObj.name}</span>
              <span className="text-[10px] text-muted-foreground font-semibold">{currentModelObj.tag}</span>
              <ChevronUp className={cn("h-3 w-3 text-muted-foreground transition-transform duration-200", modelMenuOpen && "rotate-180")} />
            </button>
          </div>

          {/* NHÓM ĐIỀU KHIỂN BÊN PHẢI: Mode Pill + Mic + Nút Gửi tròn */}
          <div className="flex items-center gap-1.5">
            {/* Pill Turbo / Mode */}
            <button
              type="button"
              onClick={() => {
                setModeMenuOpen((v) => !v);
                setModelMenuOpen(false);
                setPlusMenuOpen(false);
              }}
              className={cn(
                "inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/30 px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground active:scale-95 transition-all cursor-pointer",
                modeMenuOpen && "border-brand/50 bg-muted text-foreground"
              )}
            >
              <ShieldCheck className="h-3 w-3 text-brand" />
              <span>{isMockMode ? (isVi ? "Chạy thử" : "Mock") : "Turbo"}</span>
              <ChevronUp className={cn("h-3 w-3 text-muted-foreground transition-transform duration-200", modeMenuOpen && "rotate-180")} />
            </button>

            {/* Nút Microphone */}
            <button
              type="button"
              title={isListening ? (isVi ? "Đang nghe... bấm để dừng" : "Listening... click to stop") : (isVi ? "Nói bằng giọng nói" : "Voice dictation")}
              aria-label="Voice input"
              onClick={toggleSpeechRecognition}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full transition-all",
                isListening
                  ? "bg-semantic-danger text-white animate-pulse"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground active:scale-90"
              )}
            >
              <Mic className="h-4 w-4" />
            </button>

            {/* Nút Gửi tròn có mũi tên hướng phải -> */}
            <button
              type="button"
              disabled={disabled || !input.trim()}
              onClick={() => {
                setModelMenuOpen(false);
                setPlusMenuOpen(false);
                setModeMenuOpen(false);
                onSubmit();
              }}
              aria-label={t("sendBtn")}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full transition-all duration-200",
                input.trim() && !disabled
                  ? "bg-foreground text-background shadow-sm hover:scale-105 active:scale-95 cursor-pointer hover:bg-foreground/90"
                  : "bg-muted/70 text-muted-foreground/40 cursor-not-allowed"
              )}
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
