"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  Play,
  RotateCcw,
  Sparkles,
  Layers,
  Sliders,
  DollarSign,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Plus,
  Film,
} from "lucide-react";

export default function StudioCanvasPage() {
  const t = useTranslations("canvas");
  const { aspectRatio, setAspectRatio, isMockMode, setIsMockMode } =
    useStudioStore();

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col relative overflow-hidden bg-background">
      {/* Top Floating Action Toolbar */}
      <div className="p-3 border-b border-border bg-card/60 backdrop-blur-md flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2">
          {/* Aspect Ratio Selector */}
          <div className="flex items-center rounded-md border border-border bg-card p-0.5 text-xs">
            {(["9:16", "16:9", "1:1", "4:5"] as const).map((ratio) => (
              <button
                key={ratio}
                onClick={() => setAspectRatio(ratio)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                  aspectRatio === ratio
                    ? "bg-primary text-primary-foreground shadow-subtle"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {ratio}
              </button>
            ))}
          </div>

          {/* Mode Switcher */}
          <button
            onClick={() => setIsMockMode(!isMockMode)}
            className={`px-2.5 py-1 rounded-md text-xs font-semibold border transition-all ${
              isMockMode
                ? "bg-primary/10 border-primary/30 text-primary"
                : "bg-muted border-border text-muted-foreground"
            }`}
          >
            {isMockMode ? "Mock Mode (Miễn phí)" : "Live API (Trả phí)"}
          </button>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-md bg-muted/60 text-xs font-medium text-foreground">
            <DollarSign className="w-3.5 h-3.5 text-semantic-success" />
            <span>Ước tính: $0.12</span>
          </div>

          <Button size="sm" variant="outline">
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Reset
          </Button>

          <Button size="sm" className="shadow-subtle">
            <Play className="w-3.5 h-3.5 mr-1" />
            {t("runAll")}
          </Button>
        </div>
      </div>

      {/* Canvas Area (Sẽ tích hợp React Flow ở Bước 4) */}
      <div className="flex-1 relative bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:20px_20px] flex items-center justify-center p-6 overflow-hidden">
        {/* Placeholder Demo Node Cards showcasing the KokonutUI + React Flow UI Look */}
        <div className="flex flex-col md:flex-row items-center gap-6 z-10 max-w-4xl w-full">
          {/* Node 1: Character DNA */}
          <Card className="w-72 shadow-card border-primary/30">
            <div className="p-3 border-b border-border bg-muted/30 flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                Nhân vật Sóc Nhỏ (Bi)
              </span>
              <span className="w-2 h-2 rounded-full bg-semantic-success" />
            </div>
            <div className="p-3 text-xs space-y-2">
              <p className="text-muted-foreground">
                Tỉ lệ khóa: 100cm (1.0). Đầy đủ 18 master DNA panels.
              </p>
              <div className="p-2 rounded bg-muted/50 text-[11px] font-mono text-foreground">
                Voice-id: soc-nho
              </div>
            </div>
          </Card>

          {/* Flow Connector Arrow */}
          <div className="text-primary font-bold text-lg select-none">
            $\rightarrow$
          </div>

          {/* Node 2: Script & Prompt Generator */}
          <Card className="w-72 shadow-card">
            <div className="p-3 border-b border-border bg-muted/30 flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-primary" />
                Phân cảnh Tập 1 (45s)
              </span>
              <span className="w-2 h-2 rounded-full bg-semantic-success" />
            </div>
            <div className="p-3 text-xs space-y-2">
              <p className="text-muted-foreground">
                6 cảnh hoạt hình 3D Pixar, dạy bé đánh răng.
              </p>
              <div className="p-2 rounded bg-muted/50 text-[11px] font-mono text-foreground">
                Veo 8s per clip • 9:16
              </div>
            </div>
          </Card>

          {/* Flow Connector Arrow */}
          <div className="text-primary font-bold text-lg select-none">
            $\rightarrow$
          </div>

          {/* Node 3: HyperFrames Renderer */}
          <Card className="w-72 shadow-card border-semantic-success/30">
            <div className="p-3 border-b border-border bg-muted/30 flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Film className="w-3.5 h-3.5 text-semantic-success" />
                Hậu kỳ HyperFrames
              </span>
              <span className="w-2 h-2 rounded-full bg-semantic-success" />
            </div>
            <div className="p-3 text-xs space-y-2">
              <p className="text-muted-foreground">
                Ghép 6 cảnh, phụ đề kinetic, audio ducking -14 LUFS.
              </p>
              <div className="p-2 rounded bg-muted/50 text-[11px] font-mono text-foreground">
                MP4 1080x1920 (TikTok)
              </div>
            </div>
          </Card>
        </div>

        {/* Canvas Bottom-Right Navigation Controls */}
        <div className="absolute bottom-5 right-5 flex items-center gap-1 p-1 rounded-md border border-border bg-card/90 backdrop-blur-md shadow-card">
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <Maximize2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
