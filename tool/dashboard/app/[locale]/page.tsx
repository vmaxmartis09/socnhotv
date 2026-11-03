"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { getRepository, type Project, type Channel } from "@/lib/repositories";
import { useStudioStore } from "@/store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  Film,
  Sparkles,
  Users2,
  Tv,
  TrendingUp,
  ArrowRight,
  Layers,
  Clock,
  CheckCircle2,
} from "lucide-react";

export default function DashboardOverviewPage() {
  const t = useTranslations();
  const { activeProjectId } = useStudioStore();
  const [project, setProject] = useState<Project | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);

  useEffect(() => {
    async function load() {
      const repo = getRepository();
      const p = await repo.getProject(activeProjectId);
      const ch = await repo.listChannels();
      setProject(p);
      setChannels(ch);
    }
    load();
  }, [activeProjectId]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Hero Welcome Banner */}
      <div className="p-6 sm:p-8 rounded-xl bg-card border border-border shadow-card relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Kênh Hoạt Hình 3D & KOC AI</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            {project?.name || "Sóc Nhỏ TV"}
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {project?.description ||
              "Hệ thống sản xuất video hoạt hình 3D cho thiếu nhi & điều phối mạng xã hội tự động."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 z-10 shrink-0">
          <Link href="/studio">
            <Button size="lg" className="shadow-float">
              <Film className="w-4 h-4 mr-1.5" />
              <span>Vào Studio Canvas</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>

        {/* Subtle decorative glow */}
        <div className="absolute -right-20 -top-20 w-80 h-80 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* 3 Metric Cards (KokonutUI Style) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Card 1: Nhân vật */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Nhân vật hoạt hình</CardTitle>
            <Users2 className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {project?.charactersCount || 2} nhân vật
            </div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-semantic-success" />
              Khóa tỉ lệ: Sóc Nhỏ (100cm) & Koala (150cm)
            </p>
          </CardContent>
        </Card>

        {/* Card 2: Kênh liên kết */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Kênh phát hành</CardTitle>
            <Tv className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {channels.length} kênh kết nối
            </div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-semantic-info" />
              YouTube Data API & TikTok API
            </p>
          </CardContent>
        </Card>

        {/* Card 3: Chuẩn hậu kỳ */}
        <Card className="hover:border-primary/40 transition-colors">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Quy chuẩn Dựng & Hậu kỳ</CardTitle>
            <Layers className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">HyperFrames 9:16</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-semantic-warning" />
              Voiceover OmniVoice `soc-nho` (-14 LUFS)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Launchpad to Studio */}
      <Card>
        <CardHeader>
          <CardTitle>Quy trình sản xuất Video Canvas</CardTitle>
          <CardDescription>
            Tạo cảnh hoạt hình bằng các node liên kết chặt chẽ: Kịch bản $\rightarrow$ Ảnh tham chiếu $\rightarrow$ Video Motion $\rightarrow$ Giọng đọc Sóc Nhỏ
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 rounded-lg bg-muted/30 border border-border/50">
          <div className="space-y-1 text-sm text-foreground">
            <span className="font-semibold block">Tập phim gần nhất: Sóc Nhỏ và Chiếc Răng Sâu (45s)</span>
            <span className="text-xs text-muted-foreground block">
              6 phân cảnh • Tỉ lệ 9:16 TikTok / 16:9 YouTube • Đã biên tập bằng HyperFrames
            </span>
          </div>
          <Link href="/studio">
            <Button variant="secondary" size="md">
              Mở Canvas Tập 1
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
