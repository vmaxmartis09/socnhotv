"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useStudioStore } from "@/store";
import {
  UploadResult,
  LibraryItem,
  ParsedScene,
  uploadNodeFile,
  fetchProjectLibraryImages,
  resolveNodeFileUrl,
  parseScriptClient,
} from "@/lib/api/nodes";
import { VoiceSelectorWithClone } from "@/components/voice/VoiceSelectorWithClone";
import {
  Upload,
  Images,
  Trash2,
  ClipboardPaste,
  Maximize2,
  Sparkles,
  Plus,
  Check,
  AlertTriangle,
  FolderOpen,
  FileText,
  X,
  ChevronDown,
  ChevronUp,
  Download,
  ScrollText,
  Volume2,
  Film,
  Eye,
  Play,
} from "@/components/ui/icons";
import { cn } from "@/lib/utils";

// ============================================================================
// 1. TEXT INPUT CONTROL
// ============================================================================

interface TextInputProps {
  nodeId: string;
  content: string;
  connected?: boolean;
  connectedSource?: string;
  isDetailed?: boolean;
  /** Chế độ chỉnh sửa do card điều khiển (bấm tiêu đề để đổi) */
  expanded?: boolean;
}

export const NodeTextInput = React.memo(function NodeTextInput({
  nodeId,
  content: initialContent,
  connected,
  connectedSource,
  isDetailed,
  expanded,
}: TextInputProps) {
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const [val, setVal] = useState(initialContent || "");
  const focused = Boolean(expanded);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Tự giãn chiều cao vừa đủ nội dung khi đang focus
  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    // Đo chiều cao đích rồi trả về chiều cao cũ để CSS transition chạy mượt
    const prev = el.offsetHeight;
    el.style.height = "auto";
    const target = focused ? el.scrollHeight : Math.min(el.scrollHeight, 88);
    el.style.height = `${prev}px`;
    void el.offsetHeight;
    el.style.height = `${target}px`;
  }, [val, focused]);

  useEffect(() => {
    setVal(initialContent || "");
  }, [initialContent]);

  const handleChange = (newVal: string) => {
    setVal(newVal);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      updateNodeParams(nodeId, { content: newVal });
    }, 300);
  };

  const handlePaste = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        handleChange(text);
      }
    } catch {
      // clipboard access denied
    }
  };

  const words = val.trim() ? val.trim().split(/\s+/).length : 0;
  const chars = val.length;

  if (connected) {
    return (
      <div className="rounded-md border border-dashed border-border bg-muted/30 p-2.5 text-xs text-muted-foreground flex items-center justify-between">
        <span className="flex items-center gap-1.5 font-medium text-foreground">
          <FileText className="h-3.5 w-3.5 text-brand" />
          Nhận từ {connectedSource || "node trước"}
        </span>
        <span className="text-[11px] bg-muted px-1.5 py-0.5 rounded">Tự động</span>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="relative">
        <textarea
          ref={taRef}
          rows={1}
          value={val}
          onChange={(e) => handleChange(e.target.value)}
          onFocus={(e) => {
            // Vào chỉnh sửa: luôn đặt con trỏ ở cuối văn bản
            const el = e.currentTarget;
            requestAnimationFrame(() => {
              const end = el.value.length;
              el.setSelectionRange(end, end);
            });
          }}
          placeholder="Nhập nội dung văn bản hoặc prompt..."
          className={cn(
            "nodrag nowheel block w-full resize-none rounded-md border p-2 text-xs leading-relaxed text-foreground placeholder:text-muted-foreground/60 transition-[height,background-color,border-color,box-shadow] duration-200 ease-out focus:outline-none",
            focused
              ? "overflow-hidden border-border bg-card ring-1 ring-brand"
              : "cursor-text overflow-hidden border-transparent bg-transparent hover:border-border hover:bg-card"
          )}
        />
        {focused && (
          <button
            type="button"
            onMouseDown={(e) => e.preventDefault()}
            onClick={handlePaste}
            title="Dán từ Clipboard"
            className="nodrag absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded bg-muted/80 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ClipboardPaste className="h-3 w-3" />
          </button>
        )}
      </div>

      {focused && (
        <div className="flex items-center justify-between px-0.5 text-[11px] text-muted-foreground tnum">
          <span>{words} từ · {chars} ký tự</span>
          <span className="text-[10px] text-muted-foreground/60">Lưu tự động</span>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// 2. IMAGE INPUT CONTROL (Upload, Drag-drop, Library, URL, Ctrl+V)
// ============================================================================

interface ImageInputProps {
  nodeId: string;
  uri?: string;
  name?: string;
  nodeType?: string;
  previewUrl?: string;
  compact?: boolean;
  /** Chế độ chỉnh sửa do card điều khiển */
  expanded?: boolean;
}

export const NodeImageInput = React.memo(function NodeImageInput({
  nodeId,
  uri,
  name,
  nodeType = "image",
  previewUrl,
  compact,
  expanded,
}: ImageInputProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [libraryItems, setLibraryItems] = useState<LibraryItem[]>([]);
  const [urlInput, setUrlInput] = useState("");
  const [showUrlInput, setShowUrlInput] = useState(false);

  const currentUrl = previewUrl || resolveNodeFileUrl(activeProjectId, uri);

  const handleProcessFile = async (file: File) => {
    // Kiểm tra định dạng
    const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!validTypes.includes(file.type)) {
      setErrorMsg("Chỉ chấp nhận ảnh PNG, JPG, JPEG, WEBP");
      return;
    }
    // Giới hạn 10MB
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("Dung lượng ảnh vượt quá 10MB");
      return;
    }

    setErrorMsg(null);
    setIsUploading(true);
    try {
      const result = await uploadNodeFile(activeProjectId, file);
      updateNodeParams(nodeId, {
        uri: result.uri,
        name: result.name || file.name,
      });
    } catch (err: any) {
      setErrorMsg(err.message || "Tải ảnh thất bại");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handlePasteEvent = useCallback((e: React.ClipboardEvent | ClipboardEvent) => {
    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const f = e.clipboardData.files[0];
      if (f.type.startsWith("image/")) {
        e.preventDefault();
        handleProcessFile(f);
      }
    }
  }, [activeProjectId, nodeId]);

  const openLibraryModal = async () => {
    setShowLibrary(true);
    const items = await fetchProjectLibraryImages(activeProjectId);
    setLibraryItems(items);
  };

  const handleApplyUrl = () => {
    if (!urlInput.trim()) return;
    updateNodeParams(nodeId, { uri: urlInput.trim(), name: "url_image" });
    setShowUrlInput(false);
    setUrlInput("");
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    updateNodeParams(nodeId, { uri: "", name: "" });
  };

  return (
    <div
      className="space-y-1.5"
      onPaste={handlePasteEvent as any}
      tabIndex={0}
      style={{ outline: "none" }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleProcessFile(e.target.files[0]);
          }
        }}
      />

      {/* Hiển thị ảnh đã có */}
      {currentUrl && (
        <div className="relative group rounded-lg overflow-hidden border border-border bg-black/5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={currentUrl}
            alt={name || "Node Image"}
            loading="lazy"
            className={cn(
              "w-full object-cover object-top transition-transform group-hover:scale-[1.02]",
              compact ? "max-h-32" : "max-h-64"
            )}
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="nodrag flex items-center gap-1 rounded bg-background/90 px-2 py-1 text-[11px] font-medium text-foreground hover:bg-background transition-colors"
            >
              <Upload className="h-3 w-3" />
              Đổi ảnh
            </button>
            <button
              type="button"
              onClick={handleRemove}
              className="nodrag flex items-center gap-1 rounded bg-destructive/90 px-2 py-1 text-[11px] font-medium text-destructive-foreground hover:bg-destructive transition-colors"
            >
              <Trash2 className="h-3 w-3" />
              Xóa
            </button>
          </div>
          {name && (
            <div className="absolute bottom-1 left-1 right-1 rounded bg-background/80 px-1.5 py-0.5 text-[10px] text-foreground truncate backdrop-blur-xs">
              {name}
            </div>
          )}
        </div>
      )}

      {/* Vùng Dropzone nếu chưa có ảnh hoặc muốn tải thêm */}
      {!currentUrl && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "nodrag cursor-pointer flex flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed p-4 text-center transition-colors",
            isDragging
              ? "border-brand bg-brand/10 text-brand"
              : "border-border hover:border-brand/60 bg-muted/20 text-muted-foreground",
            compact ? "h-28" : "h-36"
          )}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand border-t-transparent" />
              <span className="text-xs font-medium text-foreground">Đang tải ảnh lên...</span>
            </div>
          ) : (
            <>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted/60 text-muted-foreground">
                <Images className="h-5 w-5" />
              </div>
              <div className="text-xs">
                <span className="font-semibold text-foreground">Kéo thả ảnh</span> hoặc{" "}
                <span className="text-brand underline">chọn tệp</span>
              </div>
              <span className="text-[10px] text-muted-foreground/70">
                Hỗ trợ Ctrl+V dán ảnh · PNG, JPG, WEBP (≤10MB)
              </span>
            </>
          )}
        </div>
      )}

      {/* Các lựa chọn phụ: Chọn Thư viện, Dán URL */}
      {!currentUrl && !isUploading && expanded && (
        <div className="flex items-center justify-between gap-1 text-[11px] pt-0.5">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              openLibraryModal();
            }}
            className="nodrag flex items-center gap-1 text-muted-foreground hover:text-foreground hover:underline"
          >
            <FolderOpen className="h-3 w-3" />
            Chọn từ Thư viện
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowUrlInput(!showUrlInput);
            }}
            className="nodrag flex items-center gap-1 text-muted-foreground hover:text-foreground hover:underline"
          >
            Dán URL ảnh
          </button>
        </div>
      )}

      {/* Ô nhập URL trực tiếp */}
      {expanded && showUrlInput && !currentUrl && (
        <div className="flex items-center gap-1 pt-1">
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://... hoặc assets/..."
            className="nodrag h-7 flex-1 rounded border border-border bg-card px-2 text-xs text-foreground placeholder:text-muted-foreground/50"
          />
          <button
            type="button"
            onClick={handleApplyUrl}
            className="nodrag h-7 rounded bg-brand px-2 text-xs font-medium text-brand-foreground hover:bg-brand/90"
          >
            Gán
          </button>
        </div>
      )}

      {/* Thông báo lỗi nếu có */}
      {errorMsg && (
        <div className="flex items-center gap-1.5 rounded-md bg-destructive/10 p-2 text-xs text-destructive">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Modal Thư viện Media */}
      {showLibrary && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setShowLibrary(false)}
        >
          <div
            className="w-full max-w-xl max-h-[80vh] flex flex-col rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border p-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FolderOpen className="h-4 w-4 text-brand" />
                Thư viện media dự án
              </h3>
              <button
                type="button"
                onClick={() => setShowLibrary(false)}
                className="rounded-md p-1 hover:bg-muted text-muted-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="p-3 overflow-y-auto flex-1">
              {libraryItems.length === 0 ? (
                <div className="py-12 text-center text-xs text-muted-foreground">
                  Chưa có ảnh nào trong thư viện media.
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2.5">
                  {libraryItems.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => {
                        updateNodeParams(nodeId, {
                          uri: item.uri || item.name,
                          name: item.name,
                        });
                        setShowLibrary(false);
                      }}
                      className="group relative cursor-pointer overflow-hidden rounded-lg border border-border hover:border-brand transition-colors aspect-video bg-black/5"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={item.url}
                        alt={item.name}
                        loading="lazy"
                        className="h-full w-full object-cover"
                      />
                      <div className="absolute inset-0 bg-brand/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <Check className="h-6 w-6 text-white drop-shadow" />
                      </div>
                      <div className="absolute bottom-0 inset-x-0 bg-background/80 p-1 text-[10px] truncate">
                        {item.name}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// 3. SCRIPT INPUT CONTROL (AI vs Paste mode, Scene Breakdown Preview)
// ============================================================================

interface ScriptInputProps {
  nodeId: string;
  mode?: "ai" | "paste";
  rawScript?: string;
  ideaText?: string;
  targetSceneCount?: number;
  targetDurationSec?: number;
  connectedText?: boolean;
}

export const NodeScriptInput = React.memo(function NodeScriptInput({
  nodeId,
  mode: initialMode = "ai",
  rawScript: initialRaw = "",
  ideaText: initialIdea = "",
  targetSceneCount = 6,
  targetDurationSec = 45,
  connectedText,
}: ScriptInputProps) {
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const [mode, setMode] = useState<"ai" | "paste">(initialMode);
  const [raw, setRaw] = useState(initialRaw);
  const [idea, setIdea] = useState(initialIdea);
  const [showHint, setShowHint] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setMode(initialMode || "ai");
  }, [initialMode]);

  useEffect(() => {
    setRaw(initialRaw || "");
  }, [initialRaw]);

  useEffect(() => {
    setIdea(initialIdea || "");
  }, [initialIdea]);

  const handleModeChange = (newMode: "ai" | "paste") => {
    setMode(newMode);
    updateNodeParams(nodeId, { mode: newMode });
  };

  const handleRawChange = (text: string) => {
    setRaw(text);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      updateNodeParams(nodeId, { rawScript: text });
    }, 300);
  };

  const handleIdeaChange = (text: string) => {
    setIdea(text);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      updateNodeParams(nodeId, { text });
    }, 300);
  };

  // Tách cảnh tức thời phía client
  const parsedScenes: ParsedScene[] = mode === "paste" && raw.trim()
    ? parseScriptClient(raw, targetSceneCount, targetDurationSec)
    : [];

  return (
    <div className="space-y-2">
      {/* Nút chuyển đổi 2 chế độ: AI vs Dán */}
      <div className="flex rounded-lg border border-border bg-muted/30 p-0.5 text-xs">
        <button
          type="button"
          onClick={() => handleModeChange("ai")}
          className={cn(
            "nodrag flex-1 flex items-center justify-center gap-1.5 py-1 rounded-md font-medium transition-all",
            mode === "ai"
              ? "bg-card text-foreground shadow-xs font-semibold"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          AI viết từ ý tưởng
        </button>
        <button
          type="button"
          onClick={() => handleModeChange("paste")}
          className={cn(
            "nodrag flex-1 flex items-center justify-center gap-1.5 py-1 rounded-md font-medium transition-all",
            mode === "paste"
              ? "bg-card text-foreground shadow-xs font-semibold"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <ScrollText className="h-3.5 w-3.5 text-brand" />
          Dán kịch bản có sẵn
        </button>
      </div>

      {/* CHẾ ĐỘ 1: AI VIẾT TỪ Ý TƯỞNG */}
      {mode === "ai" && (
        <div className="space-y-1.5">
          {connectedText ? (
            <div className="rounded-md border border-dashed border-border bg-muted/30 p-2.5 text-xs text-muted-foreground flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-foreground">
                <FileText className="h-3.5 w-3.5 text-brand" />
                Ý tưởng nhận từ dây nối
              </span>
              <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">Tự động</span>
            </div>
          ) : (
            <div className="space-y-1">
              <textarea
                rows={3}
                value={idea}
                onChange={(e) => handleIdeaChange(e.target.value)}
                placeholder="Mô tả ý tưởng kịch bản (ví dụ: Sóc Bi cùng bạn Koala khám phá hang thỏ)..."
                className="nodrag nowheel w-full rounded-md border border-border bg-card p-2 text-xs text-foreground placeholder:text-muted-foreground/60 leading-relaxed resize-y"
              />
            </div>
          )}
        </div>
      )}

      {/* CHẾ ĐỘ 2: DÁN KỊCH BẢN CÓ SẴN (TÁCH TẤT ĐỊNH KHÔNG CẦN AI) */}
      {mode === "paste" && (
        <div className="space-y-1.5">
          <textarea
            rows={5}
            value={raw}
            onChange={(e) => handleRawChange(e.target.value)}
            placeholder={`Dán kịch bản tại đây...\n\nĐịnh dạng:\nCảnh 1: Tiêu đề\nSóc Nhỏ: Lời thoại\n(Mô tả hành động)\n\nCảnh 2:\n...`}
            className="nodrag nowheel w-full rounded-md border border-border bg-card p-2 text-xs font-sans text-foreground placeholder:text-muted-foreground/50 leading-relaxed resize-y max-h-56"
          />

          {/* Hướng dẫn định dạng (accordion) */}
          <div className="border border-border/70 rounded-md bg-muted/10 overflow-hidden text-[11px]">
            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="nodrag w-full flex items-center justify-between px-2 py-1 text-muted-foreground hover:text-foreground"
            >
              <span>Chỉ dẫn định dạng kịch bản chuẩn</span>
              {showHint ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
            {showHint && (
              <div className="p-2 border-t border-border/70 space-y-1 text-muted-foreground leading-relaxed bg-background/50">
                <p>• <strong>Ngăn cảnh:</strong> Dùng dòng trống, <code className="text-foreground">---</code> hoặc dòng <code className="text-foreground">Cảnh N:</code>.</p>
                <p>• <strong>Lời thoại:</strong> Viết dạng <code className="text-foreground">Tên: Lời thoại</code> (ví dụ: <em>Sóc Nhỏ: Chào các bạn!</em>).</p>
                <p>• <strong>Mô tả / Camera:</strong> Viết trong ngoặc đơn <code className="text-foreground">(Bi vẫy tay)</code> hoặc bắt đầu bằng <code className="text-foreground">Camera:</code>.</p>
              </div>
            )}
          </div>

          {/* Thẻ xem trước phân cảnh đã nhận diện */}
          {parsedScenes.length > 0 && (
            <div className="rounded-md border border-border bg-muted/20 p-2 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1">
                  <Check className="h-3.5 w-3.5 text-semantic-success" />
                  Đã nhận diện {parsedScenes.length} cảnh ({parsedScenes.reduce((a, b) => a + b.durationSec, 0).toFixed(0)}s)
                </span>
                <button
                  type="button"
                  onClick={() => setShowPreviewModal(true)}
                  className="nodrag text-[11px] text-brand hover:underline flex items-center gap-1"
                >
                  <Eye className="h-3 w-3" />
                  Chi tiết
                </button>
              </div>
              <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
                {parsedScenes.slice(0, 3).map((sc) => (
                  <div key={sc.sceneNumber} className="rounded bg-card/60 p-1.5 text-[11px] border border-border/60">
                    <div className="font-semibold text-foreground">{sc.title} <span className="text-muted-foreground font-normal">({sc.durationSec}s)</span></div>
                    {sc.dialogue && <div className="text-muted-foreground truncate">💬 {sc.dialogue}</div>}
                  </div>
                ))}
                {parsedScenes.length > 3 && (
                  <div className="text-[10px] text-center text-muted-foreground">
                    + {parsedScenes.length - 3} cảnh khác
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal xem toàn bộ phân cảnh */}
      {showPreviewModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setShowPreviewModal(false)}
        >
          <div
            className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-xl border border-border bg-card shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border p-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <ScrollText className="h-4 w-4 text-brand" />
                Danh sách {parsedScenes.length} phân cảnh đã tách
              </h3>
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                className="rounded-md p-1 hover:bg-muted text-muted-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="p-3.5 overflow-y-auto space-y-2.5 flex-1">
              {parsedScenes.map((sc) => (
                <div key={sc.sceneNumber} className="rounded-lg border border-border bg-background p-3 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between border-b border-border/60 pb-1">
                    <span className="font-semibold text-foreground">{sc.title}</span>
                    <span className="text-muted-foreground tnum">{sc.durationSec}s</span>
                  </div>
                  {sc.dialogue && (
                    <div className="text-foreground">
                      <span className="font-medium text-brand">Thoại: </span>
                      {sc.dialogue}
                    </div>
                  )}
                  <div className="text-muted-foreground">
                    <span className="font-medium text-foreground">Hình ảnh: </span>
                    {sc.imagePrompt}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// 4. VOICE INPUT CONTROL (Direct speech text, VoiceSelectorWithClone, tempo)
// ============================================================================

interface VoiceInputProps {
  nodeId: string;
  text?: string;
  voiceId?: string;
  tempo?: number;
  connectedText?: boolean;
}

export const NodeVoiceInput = React.memo(function NodeVoiceInput({
  nodeId,
  text: initialText = "",
  voiceId = "soc-nho",
  tempo = 1.1,
  connectedText,
}: VoiceInputProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const [val, setVal] = useState(initialText);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setVal(initialText || "");
  }, [initialText]);

  const handleTextChange = (newVal: string) => {
    setVal(newVal);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      updateNodeParams(nodeId, { text: newVal });
    }, 300);
  };

  return (
    <div className="space-y-2">
      {/* Lời thoại cần đọc */}
      {connectedText ? (
        <div className="rounded-md border border-dashed border-border bg-muted/30 p-2 text-xs text-muted-foreground flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-medium text-foreground">
            <Volume2 className="h-3.5 w-3.5 text-brand" />
            Lời thoại nhận từ kịch bản
          </span>
          <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">Tự động</span>
        </div>
      ) : (
        <textarea
          rows={2}
          value={val}
          onChange={(e) => handleTextChange(e.target.value)}
          placeholder="Nhập lời thoại cần đọc trực tiếp..."
          className="nodrag nowheel w-full rounded-md border border-border bg-card p-2 text-xs text-foreground placeholder:text-muted-foreground/60 leading-relaxed resize-y"
        />
      )}

      {/* Bộ chọn giọng OmniVoice */}
      <div className="nodrag">
        <VoiceSelectorWithClone
          value={voiceId}
          onChange={(vid) => updateNodeParams(nodeId, { voiceId: vid })}
          projectId={activeProjectId}
        />
      </div>
    </div>
  );
});

// ============================================================================
// 5. IMAGE GEN INPUT CONTROL (Prompt + Multiple Reference Images)
// ============================================================================

interface ImageGenInputProps {
  nodeId: string;
  prompt?: string;
  referenceImages?: string[];
  aspectRatio?: string;
  model?: string;
  connectedPrompt?: boolean;
}

export const NodeImageGenInput = React.memo(function NodeImageGenInput({
  nodeId,
  prompt: initialPrompt = "",
  referenceImages = [],
  aspectRatio = "9:16",
  model = "gemini-2.5-flash-image",
  connectedPrompt,
}: ImageGenInputProps) {
  const activeProjectId = useStudioStore((s) => s.activeProjectId);
  const characters = useStudioStore((s) => s.characters);
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const [val, setVal] = useState(initialPrompt);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setVal(initialPrompt || "");
  }, [initialPrompt]);

  const handlePromptChange = (newVal: string) => {
    setVal(newVal);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      updateNodeParams(nodeId, { prompt: newVal });
    }, 300);
  };

  const handleAddReferenceFile = async (file: File) => {
    try {
      const res = await uploadNodeFile(activeProjectId, file);
      const next = [...(referenceImages || []), res.uri];
      updateNodeParams(nodeId, { referenceImages: next });
    } catch {
      // upload error
    }
  };

  const handleRemoveRef = (idx: number) => {
    const next = [...referenceImages];
    next.splice(idx, 1);
    updateNodeParams(nodeId, { referenceImages: next });
  };

  return (
    <div className="space-y-2">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleAddReferenceFile(e.target.files[0]);
          }
        }}
      />

      {/* Prompt */}
      {connectedPrompt ? (
        <div className="rounded-md border border-dashed border-border bg-muted/30 p-2 text-xs text-muted-foreground flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-medium text-foreground">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            Prompt nhận từ phân cảnh
          </span>
          <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded">Tự động</span>
        </div>
      ) : (
        <textarea
          rows={3}
          value={val}
          onChange={(e) => handlePromptChange(e.target.value)}
          placeholder="Mô tả hình ảnh tạo mới..."
          className="nodrag nowheel w-full rounded-md border border-border bg-card p-2 text-xs text-foreground placeholder:text-muted-foreground/60 leading-relaxed resize-y"
        />
      )}

      {/* Ảnh mẫu tham chiếu DNA (Reference Images) */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>Ảnh mẫu tham chiếu ({referenceImages.length})</span>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="nodrag text-brand hover:underline flex items-center gap-0.5"
          >
            <Plus className="h-3 w-3" />
            Thêm ảnh
          </button>
        </div>

        {referenceImages.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {referenceImages.map((uri, idx) => {
              const u = resolveNodeFileUrl(activeProjectId, uri);
              return (
                <div key={idx} className="relative group h-12 w-12 rounded border border-border overflow-hidden bg-muted/40">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={u} alt="" className="h-full w-full object-cover object-top" />
                  <button
                    type="button"
                    onClick={() => handleRemoveRef(idx)}
                    className="nodrag absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tỉ lệ khung hình */}
      <div className="flex items-center justify-between text-xs pt-0.5">
        <span className="text-muted-foreground">Tỉ lệ:</span>
        <select
          value={aspectRatio}
          onChange={(e) => updateNodeParams(nodeId, { aspectRatio: e.target.value })}
          className="nodrag h-7 rounded border border-border bg-card px-2 text-xs text-foreground"
        >
          <option value="9:16">9:16 (Dọc TikTok)</option>
          <option value="16:9">16:9 (Ngang)</option>
          <option value="1:1">1:1 (Vuông)</option>
        </select>
      </div>
    </div>
  );
});

// ============================================================================
// 6. EXPORT INPUT CONTROL (Platform checkboxes, file name, download)
// ============================================================================

interface ExportInputProps {
  nodeId: string;
  outputFileName?: string;
  platforms?: string[];
  previewUrl?: string;
}

export const NodeExportInput = React.memo(function NodeExportInput({
  nodeId,
  outputFileName = "final_video.mp4",
  platforms = ["tiktok", "youtube"],
  previewUrl,
}: ExportInputProps) {
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);
  const [name, setName] = useState(outputFileName);

  const togglePlatform = (p: string) => {
    const set = new Set(platforms);
    if (set.has(p)) set.delete(p);
    else set.add(p);
    updateNodeParams(nodeId, { platforms: Array.from(set) });
  };

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <label className="text-[11px] text-muted-foreground block">Tên file xuất bản</label>
        <input
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            updateNodeParams(nodeId, { outputFileName: e.target.value });
          }}
          className="nodrag h-7 w-full rounded border border-border bg-card px-2 font-mono text-xs text-foreground"
        />
      </div>

      <div className="space-y-1">
        <span className="text-[11px] text-muted-foreground block">Nền tảng xuất:</span>
        <div className="flex flex-wrap gap-1.5">
          {["tiktok", "youtube", "facebook", "instagram"].map((p) => {
            const active = platforms.includes(p);
            return (
              <button
                key={p}
                type="button"
                onClick={() => togglePlatform(p)}
                className={cn(
                  "nodrag text-[10px] rounded px-2 py-0.5 border transition-colors capitalize",
                  active
                    ? "bg-brand/10 border-brand text-brand font-medium"
                    : "border-border text-muted-foreground hover:bg-muted"
                )}
              >
                {p}
              </button>
            );
          })}
        </div>
      </div>

      {previewUrl && (
        <div className="space-y-1.5 pt-1 border-t border-border/80">
          <div className="rounded bg-emerald-500/10 border border-emerald-500/30 p-2 text-[11px] text-emerald-400 font-mono">
            <span className="font-semibold block text-emerald-300">✓ Đã lưu thành phẩm:</span>
            <span className="break-all">
              {previewUrl.includes("output/")
                ? previewUrl.slice(previewUrl.indexOf("output/"))
                : `output/${outputFileName}`}
            </span>
          </div>
          <div className="flex gap-1.5">
            <a
              href={previewUrl}
              target="_blank"
              rel="noreferrer"
              className="nodrag flex-1 flex items-center justify-center gap-1 rounded bg-accent py-1 text-[11px] font-medium text-foreground hover:bg-accent/80 transition-colors"
            >
              <Play className="h-3 w-3 text-primary" />
              Xem video
            </a>
            <a
              href={previewUrl}
              download={outputFileName}
              className="nodrag flex-1 flex items-center justify-center gap-1 rounded bg-brand py-1 text-[11px] font-semibold text-brand-foreground hover:bg-brand/90 transition-colors shadow-xs"
            >
              <Download className="h-3 w-3" />
              Tải MP4
            </a>
          </div>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// 7. CHARACTER SELECT CONTROL
// ============================================================================

interface CharacterSelectProps {
  nodeId: string;
  characterId?: string;
}

export const NodeCharacterSelect = React.memo(function NodeCharacterSelect({ characterId = "soc_nho", onOpen }: CharacterSelectProps & { onOpen?: () => void }) {
  const characters = useStudioStore((s) => s.characters);
  const cur = characters.find((c) => c.id === characterId);
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onOpen?.();
      }}
      className="nodrag flex h-8 w-full items-center justify-between rounded border border-border bg-card px-2 text-xs text-foreground transition-colors hover:bg-accent"
    >
      <span className="truncate">Đổi nhân vật{cur ? ` · ${cur.name}` : ""}</span>
      <span aria-hidden>›</span>
    </button>
  );
});

// ============================================================================
// 8. CAPTIONS INPUT CONTROL
// ============================================================================

interface CaptionsInputProps {
  nodeId: string;
  style?: string;
  language?: string;
}

export const NodeCaptionsInput = React.memo(function NodeCaptionsInput({
  nodeId,
  style = "kinetic_karaoke",
  language = "vi",
}: CaptionsInputProps) {
  const updateNodeParams = useStudioStore((s) => s.updateNodeParams);

  return (
    <div className="grid grid-cols-2 gap-2 text-xs">
      <div className="space-y-1">
        <span className="text-[11px] text-muted-foreground block">Kiểu phụ đề</span>
        <select
          value={style}
          onChange={(e) => updateNodeParams(nodeId, { style: e.target.value })}
          className="nodrag h-7 w-full rounded border border-border bg-card px-2 text-xs text-foreground"
        >
          <option value="kinetic_karaoke">Karaoke nảy chữ</option>
          <option value="clean_bottom">Dưới đáy tối giản</option>
          <option value="pop_bounce">Pop Bounce nổi</option>
        </select>
      </div>
      <div className="space-y-1">
        <span className="text-[11px] text-muted-foreground block">Ngôn ngữ</span>
        <select
          value={language}
          onChange={(e) => updateNodeParams(nodeId, { language: e.target.value })}
          className="nodrag h-7 w-full rounded border border-border bg-card px-2 text-xs text-foreground"
        >
          <option value="vi">Tiếng Việt (vi)</option>
          <option value="en">English (en)</option>
        </select>
      </div>
    </div>
  );
});
