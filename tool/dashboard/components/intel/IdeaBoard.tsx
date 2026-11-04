"use client";

import React, { useState, useEffect } from "react";
import {
  DndContext,
  DragEndEvent,
  useDraggable,
  useDroppable,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import type { ContentIdea, IdeaStatus } from "@/lib/api/intel";
import { intelApi } from "@/lib/api/intel";
import {
  Sparkles,
  Star,
  Send,
  Wand2,
  Calendar,
  Layers,
  CheckCircle,
} from "./icons";
import { Loader2, Plus } from "@/components/ui/icons";

interface IdeaBoardProps {
  projectId: string;
}

const COLUMNS: Array<{ id: IdeaStatus; title: string; color: string; badgeBg: string }> = [
  { id: "new", title: "Mới sinh (New)", color: "border-indigo-500/40", badgeBg: "bg-indigo-500/10 text-indigo-400" },
  { id: "scripted", title: "Đã viết kịch bản", color: "border-purple-500/40", badgeBg: "bg-purple-500/10 text-purple-400" },
  { id: "rendered", title: "Đã dựng xong", color: "border-teal-500/40", badgeBg: "bg-teal-500/10 text-teal-400" },
  { id: "scheduled", title: "Đã lên lịch đăng", color: "border-emerald-500/40", badgeBg: "bg-emerald-500/10 text-emerald-400" },
];

function KanbanCard({
  idea,
  onPromote,
  onSchedule,
}: {
  idea: ContentIdea;
  onPromote: (id: string) => void;
  onSchedule: (id: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: idea.id,
    data: { idea },
  });

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 50,
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`group rounded-xl border border-zinc-800 bg-zinc-950 p-3.5 shadow-md transition hover:border-zinc-700 cursor-grab active:cursor-grabbing ${
        isDragging ? "opacity-50 ring-2 ring-indigo-500 scale-105" : ""
      }`}
    >
      <div className="flex items-center justify-between text-[11px] mb-1.5">
        <span className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400 truncate max-w-[120px]">
          {idea.template_id || "template-v1"}
        </span>
        <div className="flex items-center gap-0.5 text-amber-400">
          <Star className="h-3 w-3 fill-amber-400" />
          <span className="font-bold text-[10px]">{idea.priority}</span>
        </div>
      </div>

      <h4 className="text-xs font-semibold text-zinc-100 leading-snug line-clamp-2">
        {idea.title}
      </h4>

      {/* Platform pills */}
      <div className="mt-2.5 flex flex-wrap gap-1">
        {idea.platform_targets.slice(0, 3).map((p) => (
          <span
            key={p}
            className="rounded bg-zinc-900 px-1.5 py-0.5 text-[9px] font-medium uppercase text-zinc-400 border border-zinc-800/80"
          >
            {p}
          </span>
        ))}
      </div>

      {/* Actions row */}
      <div className="mt-3 pt-2.5 border-t border-zinc-800/60 flex items-center justify-end gap-1.5">
        {idea.status === "new" && (
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => onPromote(idea.id)}
            className="inline-flex items-center gap-1 rounded-md bg-indigo-600/20 px-2 py-1 text-[10px] font-bold text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30"
          >
            <Wand2 className="h-3 w-3" /> Viết kịch bản
          </button>
        )}

        {(idea.status === "scripted" || idea.status === "rendered") && (
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => onSchedule(idea.id)}
            className="inline-flex items-center gap-1 rounded-md bg-emerald-600/20 px-2 py-1 text-[10px] font-bold text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30"
          >
            <Send className="h-3 w-3" /> Lên lịch
          </button>
        )}
      </div>
    </div>
  );
}

function KanbanColumn({
  col,
  ideas,
  onPromote,
  onSchedule,
}: {
  col: (typeof COLUMNS)[number];
  ideas: ContentIdea[];
  onPromote: (id: string) => void;
  onSchedule: (id: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: col.id,
  });

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col rounded-2xl border bg-zinc-900/30 p-3.5 min-h-[500px] transition ${col.color} ${
        isOver ? "bg-indigo-950/20 border-indigo-500 ring-1 ring-indigo-500/50" : ""
      }`}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between pb-3 border-b border-zinc-800/60 mb-3">
        <h3 className="text-xs font-bold text-zinc-200">{col.title}</h3>
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${col.badgeBg}`}>
          {ideas.length}
        </span>
      </div>

      {/* Cards list */}
      <div className="flex-1 space-y-2.5 overflow-y-auto">
        {ideas.map((idea) => (
          <KanbanCard
            key={idea.id}
            idea={idea}
            onPromote={onPromote}
            onSchedule={onSchedule}
          />
        ))}

        {ideas.length === 0 && (
          <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-zinc-800/60 text-center text-[11px] text-zinc-500">
            Kéo thả ý tưởng vào đây
          </div>
        )}
      </div>
    </div>
  );
}

export function IdeaBoard({ projectId }: IdeaBoardProps) {
  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  );

  const loadIdeas = async () => {
    try {
      setLoading(true);
      const data = await intelApi.listIdeas(projectId);
      setIdeas(data);
    } catch (err) {
      console.error("Failed to load ideas:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIdeas();
  }, [projectId]);

  const handleGenerateBatch = async () => {
    setIsGenerating(true);
    try {
      const generated = await intelApi.generateIdeas(projectId, 30);
      setIdeas((prev) => [...prev, ...generated]);
    } catch (err: any) {
      alert(`Lỗi sinh ý tưởng: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const ideaId = active.id as string;
    const targetStatus = over.id as IdeaStatus;

    // Optimistic update
    setIdeas((prev) =>
      prev.map((i) => (i.id === ideaId ? { ...i, status: targetStatus } : i))
    );

    try {
      await intelApi.updateIdea(projectId, ideaId, { status: targetStatus });
    } catch (err: any) {
      alert(`Lỗi cập nhật trạng thái ý tưởng: ${err.message}`);
      loadIdeas();
    }
  };

  const handlePromote = async (id: string) => {
    try {
      await intelApi.promoteIdea(projectId, id);
      setIdeas((prev) =>
        prev.map((i) => (i.id === id ? { ...i, status: "scripted" } : i))
      );
    } catch (err: any) {
      alert(`Lỗi viết kịch bản: ${err.message}`);
    }
  };

  const handleSchedule = async (id: string) => {
    try {
      await intelApi.scheduleIdea(projectId, id);
      setIdeas((prev) =>
        prev.map((i) => (i.id === id ? { ...i, status: "scheduled" } : i))
      );
    } catch (err: any) {
      alert(`Lỗi lên lịch đăng: ${err.message}`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Board Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            Bảng Ý Tưởng Nội Dung (Content Kanban)
          </h2>
          <p className="text-xs text-zinc-400">
            Tổng cộng <span className="font-semibold text-zinc-200">{ideas.length}</span> ý tưởng sẵn sàng chuyển hoá thành video và đưa lên lịch đăng
          </p>
        </div>

        <button
          onClick={handleGenerateBatch}
          disabled={isGenerating}
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 disabled:opacity-50 transition"
        >
          {isGenerating ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Sparkles className="h-3.5 w-3.5" />
          )}
          Sinh 30 ý tưởng AI
        </button>
      </div>

      {/* Kanban Grid */}
      {loading ? (
        <div className="flex h-64 items-center justify-center text-zinc-500">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
          <span className="text-xs">Đang tải bảng ý tưởng...</span>
        </div>
      ) : (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {COLUMNS.map((col) => (
              <KanbanColumn
                key={col.id}
                col={col}
                ideas={ideas.filter((i) => i.status === col.id)}
                onPromote={handlePromote}
                onSchedule={handleSchedule}
              />
            ))}
          </div>
        </DndContext>
      )}
    </div>
  );
}
