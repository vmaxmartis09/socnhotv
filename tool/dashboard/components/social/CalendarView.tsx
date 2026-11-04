"use client";

import React, { useState, useMemo } from "react";
import {
  format,
  addMonths,
  subMonths,
  addWeeks,
  subWeeks,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  parseISO,
} from "date-fns";
import { vi } from "date-fns/locale";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  useDroppable,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import { useSocialStore } from "@/store/modules/social";
import { CalendarItem, CalendarNote } from "@/lib/api/social";
import { PostChip } from "./PostChip";
import { AgendaList } from "./AgendaList";
import {
  Calendar,
  CalendarDays,
  ListOrdered,
  Plus,
  RotateCcw,
  Sparkles,
} from "@/components/ui/icons";
import { Clock } from "./icons";

interface CalendarViewProps {
  projectId: string;
}

// Droppable Day Cell for Month View
function DayCell({
  date,
  currentMonth,
  items,
  notes,
  onItemClick,
  onAddClick,
}: {
  date: Date;
  currentMonth: Date;
  items: CalendarItem[];
  notes: CalendarNote[];
  onItemClick: (item: CalendarItem) => void;
  onAddClick: (dateStr: string) => void;
}) {
  const dateStr = format(date, "yyyy-MM-dd");
  const { setNodeRef, isOver } = useDroppable({
    id: `droppable_day_${dateStr}`,
    data: { dateStr },
  });

  const inCurrentMonth = isSameMonth(date, currentMonth);
  const today = isToday(date);
  const dayNotes = notes.filter((n) => n.date === dateStr);

  const maxVisible = 3;
  const visibleItems = items.slice(0, maxVisible);
  const remaining = items.length - maxVisible;

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "group relative flex min-h-[110px] flex-col rounded-lg border p-1.5 transition-colors",
        inCurrentMonth ? "bg-card border-border" : "bg-muted/30 border-border/40 opacity-60",
        isOver && "border-primary bg-primary/5 ring-2 ring-primary/30",
        today && "ring-1 ring-primary/60 border-primary/50"
      )}
    >
      {/* Date Header & Notes */}
      <div className="flex items-center justify-between pb-1">
        <span
          className={cn(
            "flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold",
            today
              ? "bg-primary text-primary-foreground font-bold shadow-xs"
              : "text-muted-foreground group-hover:text-foreground"
          )}
        >
          {format(date, "d")}
        </span>

        <button
          onClick={() => onAddClick(dateStr)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
          title={`Thêm bài viết ngày ${dateStr}`}
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Notes Badges */}
      {dayNotes.length > 0 && (
        <div className="mb-1 space-y-0.5">
          {dayNotes.map((n) => (
            <div
              key={n.id}
              style={{ backgroundColor: `${n.color || "#f59e0b"}20`, borderColor: n.color || "#f59e0b" }}
              className="line-clamp-1 rounded border px-1 text-[10px] font-medium text-foreground"
              title={n.text}
            >
              {n.text}
            </div>
          ))}
        </div>
      )}

      {/* Post Chips */}
      <div className="flex flex-1 flex-col gap-1 overflow-hidden">
        {visibleItems.map((item) => (
          <PostChip key={item.target_id} item={item} onClick={onItemClick} compact />
        ))}
        {remaining > 0 && (
          <div className="text-[10px] font-semibold text-muted-foreground pl-1 hover:text-foreground cursor-pointer">
            +{remaining} bài khác
          </div>
        )}
      </div>
    </div>
  );
}

// Droppable Hour Cell for Week View
function WeekHourCell({
  dateStr,
  hour,
  isGolden,
  items,
  onSlotClick,
  onItemClick,
}: {
  dateStr: string;
  hour: number;
  isGolden: boolean;
  items: CalendarItem[];
  onSlotClick: (dateStr: string, hourStr: string) => void;
  onItemClick: (item: CalendarItem) => void;
}) {
  const hourStr = `${hour.toString().padStart(2, "0")}:00`;
  const { setNodeRef, isOver } = useDroppable({
    id: `droppable_week_${dateStr}_${hourStr}`,
    data: { dateStr, hourStr },
  });

  return (
    <div
      ref={setNodeRef}
      onClick={() => onSlotClick(dateStr, hourStr)}
      className={cn(
        "relative min-h-[44px] border-b border-r border-border/50 p-1 transition-colors cursor-pointer",
        isGolden &&
          "bg-[repeating-linear-gradient(45deg,transparent,transparent_8px,rgba(234,179,8,0.06)_8px,rgba(234,179,8,0.06)_16px)]",
        isOver && "bg-primary/10 ring-1 ring-primary",
        "hover:bg-muted/40"
      )}
    >
      {isGolden && items.length === 0 && (
        <span className="absolute bottom-1 right-1 text-[9px] font-mono font-medium text-amber-500/70">
          Khung vàng
        </span>
      )}
      <div className="flex flex-col gap-1">
        {items.map((item) => (
          <PostChip key={item.target_id} item={item} onClick={onItemClick} compact />
        ))}
      </div>
    </div>
  );
}

export function CalendarView({ projectId }: CalendarViewProps) {
  const {
    calendarData,
    calendarView,
    setCalendarView,
    selectedDate,
    setSelectedDate,
    moveTargetTime,
    undoLastDrag,
    lastDragAction,
    openComposer,
  } = useSocialStore();

  const [activeDragItem, setActiveDragItem] = useState<CalendarItem | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const currentDate = useMemo(() => {
    try {
      return parseISO(selectedDate);
    } catch {
      return new Date();
    }
  }, [selectedDate]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const item = event.active.data.current?.item as CalendarItem;
    if (item) setActiveDragItem(item);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveDragItem(null);

    if (!over) return;
    const item = active.data.current?.item as CalendarItem;
    if (!item) return;

    let targetDateStr: string | null = null;
    let targetTimeStr: string | null = null;

    if (over.data.current?.dateStr) {
      targetDateStr = over.data.current.dateStr;
    }
    if (over.data.current?.hourStr) {
      targetTimeStr = over.data.current.hourStr;
    }

    if (!targetDateStr) return;

    // Retain existing hour if dropping in month view
    const existingTime = item.scheduled_at?.slice(11, 16) || "19:00";
    const finalTime = targetTimeStr || existingTime;
    const newScheduledAt = `${targetDateStr}T${finalTime}:00+07:00`;

    if (newScheduledAt === item.scheduled_at) return;

    try {
      await moveTargetTime(projectId, item.post_id, item.target_id, newScheduledAt);
      setToastMessage(`Đã đổi lịch sang ${format(parseISO(newScheduledAt), "HH:mm dd/MM")}`);
      setTimeout(() => setToastMessage(null), 5000);
    } catch (err: any) {
      alert(`Không thể đổi lịch: ${err.message}`);
    }
  };

  // Month navigation
  const handlePrev = () => {
    if (calendarView === "month") {
      setSelectedDate(format(subMonths(currentDate, 1), "yyyy-MM-dd"));
    } else {
      setSelectedDate(format(subWeeks(currentDate, 1), "yyyy-MM-dd"));
    }
  };

  const handleNext = () => {
    if (calendarView === "month") {
      setSelectedDate(format(addMonths(currentDate, 1), "yyyy-MM-dd"));
    } else {
      setSelectedDate(format(addWeeks(currentDate, 1), "yyyy-MM-dd"));
    }
  };

  const handleToday = () => {
    setSelectedDate(format(new Date(), "yyyy-MM-dd"));
  };

  // Month Days calculation
  const monthDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: startDate, end: endDate });
  }, [currentDate]);

  // Week Days calculation
  const weekDays = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
    const weekEnd = endOfWeek(weekStart, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: weekStart, end: weekEnd });
  }, [currentDate]);

  const items = calendarData?.items || [];
  const notes = calendarData?.notes || [];
  const emptySlots = calendarData?.empty_slots || [];

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex flex-col h-full space-y-4">
        {/* Navigation & Toolbar Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-2xs">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-foreground min-w-[160px]">
              {calendarView === "month"
                ? format(currentDate, "MMMM, yyyy", { locale: vi })
                : `Tuần ${format(weekDays[0], "dd/MM")} - ${format(weekDays[6], "dd/MM/yyyy")}`}
            </h2>
            <div className="flex items-center gap-1">
              <button
                onClick={handlePrev}
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-muted text-foreground text-sm font-bold"
              >
                ‹
              </button>
              <button
                onClick={handleToday}
                className="rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted text-foreground"
              >
                Hôm nay
              </button>
              <button
                onClick={handleNext}
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-muted text-foreground text-sm font-bold"
              >
                ›
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Timezone badge */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg font-mono">
              <Clock className="h-3.5 w-3.5" />
              <span>Asia/Ho_Chi_Minh (UTC+7)</span>
            </div>

            {/* Segmented View Switcher */}
            <div className="flex rounded-lg border border-border bg-muted/40 p-0.5 text-xs">
              <button
                onClick={() => setCalendarView("month")}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1 font-medium transition-all",
                  calendarView === "month"
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Calendar className="h-3.5 w-3.5" />
                <span>Tháng</span>
              </button>
              <button
                onClick={() => setCalendarView("week")}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1 font-medium transition-all",
                  calendarView === "week"
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <CalendarDays className="h-3.5 w-3.5" />
                <span>Tuần</span>
              </button>
              <button
                onClick={() => setCalendarView("agenda")}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1 font-medium transition-all",
                  calendarView === "agenda"
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <ListOrdered className="h-3.5 w-3.5" />
                <span>Danh sách</span>
              </button>
            </div>
          </div>
        </div>

        {/* Undo Toast Notification */}
        {lastDragAction && toastMessage && (
          <div className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary/10 px-4 py-2 text-xs font-medium text-primary shadow-xs">
            <span>{toastMessage}</span>
            <button
              onClick={() => undoLastDrag(projectId)}
              className="flex items-center gap-1 underline hover:opacity-80 font-bold"
            >
              <RotateCcw className="h-3 w-3" />
              Hoàn tác
            </button>
          </div>
        )}

        {/* Calendar Body: Month View */}
        {calendarView === "month" && (
          <div className="flex-1 rounded-xl border border-border bg-card p-3 shadow-2xs">
            <div className="grid grid-cols-7 gap-2 mb-2 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Thứ 2</span>
              <span>Thứ 3</span>
              <span>Thứ 4</span>
              <span>Thứ 5</span>
              <span>Thứ 6</span>
              <span className="text-primary/70">Thứ 7</span>
              <span className="text-primary/70">Chủ nhật</span>
            </div>
            <div className="grid grid-cols-7 gap-2">
              {monthDays.map((date) => {
                const dateStr = format(date, "yyyy-MM-dd");
                const dayItems = items.filter(
                  (i) => i.scheduled_at && i.scheduled_at.startsWith(dateStr)
                );
                return (
                  <DayCell
                    key={dateStr}
                    date={date}
                    currentMonth={currentDate}
                    items={dayItems}
                    notes={notes}
                    onItemClick={() => openComposer(null, dateStr)}
                    onAddClick={(d) => openComposer(null, d)}
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Calendar Body: Week View (Hourly Grid) */}
        {calendarView === "week" && (
          <div className="flex-1 overflow-x-auto rounded-xl border border-border bg-card shadow-2xs">
            <div className="min-w-[800px]">
              {/* Day Headers */}
              <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-border bg-muted/30 text-xs font-semibold">
                <div className="p-2 text-center text-muted-foreground">Giờ</div>
                {weekDays.map((day) => {
                  const today = isToday(day);
                  return (
                    <div
                      key={day.toISOString()}
                      className={cn(
                        "p-2 text-center border-l border-border",
                        today && "text-primary font-bold bg-primary/5"
                      )}
                    >
                      <div>{format(day, "EEEE", { locale: vi })}</div>
                      <div className="text-xs font-mono text-muted-foreground">{format(day, "dd/MM")}</div>
                    </div>
                  );
                })}
              </div>

              {/* 24-Hour Grid */}
              <div className="max-h-[600px] overflow-y-auto">
                {Array.from({ length: 24 }).map((_, hour) => (
                  <div key={hour} className="grid grid-cols-[60px_repeat(7,1fr)]">
                    <div className="border-b border-r border-border/40 p-1 text-center font-mono text-[10px] text-muted-foreground">
                      {hour.toString().padStart(2, "0")}:00
                    </div>
                    {weekDays.map((day) => {
                      const dateStr = format(day, "yyyy-MM-dd");
                      const weekday = day.getDay() === 0 ? 6 : day.getDay() - 1; // 0=Mon, 6=Sun
                      const hourStr = `${hour.toString().padStart(2, "0")}:00`;

                      // Check if golden slot
                      const isGolden = emptySlots.some(
                        (s) =>
                          s.weekday === weekday &&
                          parseInt(s.start.slice(0, 2), 10) <= hour &&
                          parseInt(s.end.slice(0, 2), 10) > hour
                      );

                      const slotItems = items.filter((i) => {
                        if (!i.scheduled_at) return false;
                        return (
                          i.scheduled_at.startsWith(dateStr) &&
                          parseInt(i.scheduled_at.slice(11, 13), 10) === hour
                        );
                      });

                      return (
                        <WeekHourCell
                          key={`${dateStr}_${hour}`}
                          dateStr={dateStr}
                          hour={hour}
                          isGolden={isGolden}
                          items={slotItems}
                          onSlotClick={(d, h) => openComposer(null, `${d}T${h}:00+07:00`)}
                          onItemClick={() => openComposer(null)}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Calendar Body: Agenda View */}
        {calendarView === "agenda" && (
          <div className="flex-1 rounded-xl border border-border bg-card p-4 shadow-2xs">
            <AgendaList
              items={items}
              onItemClick={() => openComposer(null)}
              emptyMessage="Không có bài viết nào trong khoảng thời gian này."
            />
          </div>
        )}

        {/* Drag Overlay Avatar */}
        <DragOverlay>
          {activeDragItem ? (
            <div className="w-48 shadow-xl opacity-90 scale-105">
              <PostChip item={activeDragItem} compact />
            </div>
          ) : null}
        </DragOverlay>
      </div>
    </DndContext>
  );
}
