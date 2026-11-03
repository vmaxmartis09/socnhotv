"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { getRepository, type Character } from "@/lib/repositories";
import { useStudioStore } from "@/store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Users2, Plus, Sparkles, Ruler, Volume2, Brain } from "lucide-react";

export default function CharactersPage() {
  const t = useTranslations();
  const { activeProjectId } = useStudioStore();
  const [characters, setCharacters] = useState<Character[]>([]);

  useEffect(() => {
    async function load() {
      const repo = getRepository();
      const list = await repo.listCharacters(activeProjectId);
      setCharacters(list);
    }
    load();
  }, [activeProjectId]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-foreground">
            Nhân vật & Bộ Nhớ Nhân Vật (Character Bible)
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Khóa hình ảnh DNA, tỉ lệ chiều cao và bộ nhớ tính cách để nhân vật nhất quán qua từng tập phim
          </p>
        </div>

        <Button size="md">
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Thêm nhân vật mới</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {characters.map((char) => (
          <Card key={char.id} className="overflow-hidden">
            <CardHeader className="bg-muted/20 border-b border-border/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                    {char.name.charAt(0)}
                  </div>
                  <div>
                    <CardTitle className="text-base">{char.name}</CardTitle>
                    <CardDescription className="text-xs">
                      Vai trò: {char.role === "main" ? "Nhân vật chính" : "Nhân vật phụ"}
                    </CardDescription>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-card border border-border text-xs font-semibold text-foreground">
                  <Ruler className="w-3.5 h-3.5 text-primary" />
                  <span>{char.heightCm} cm ({char.scaleRatio}x)</span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-5 space-y-4 text-xs">
              {/* Voice ID */}
              <div className="flex items-center gap-2 text-muted-foreground">
                <Volume2 className="w-4 h-4 text-semantic-warning shrink-0" />
                <span>Giọng đọc OmniVoice:</span>
                <span className="font-mono font-semibold text-foreground bg-muted px-2 py-0.5 rounded">
                  {char.voiceId}
                </span>
              </div>

              {/* Prompt Lock */}
              <div className="space-y-1">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  Prompt Lock (Khóa nhận diện ngoại hình):
                </span>
                <p className="p-2.5 rounded-md bg-muted/40 font-mono text-[11px] text-muted-foreground leading-relaxed border border-border/50">
                  {char.promptLock}
                </p>
              </div>

              {/* Character Memory */}
              <div className="space-y-2 pt-2 border-t border-border/60">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-semantic-info" />
                  Bộ nhớ nhân vật (Character Memory):
                </span>

                <div className="grid grid-cols-1 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-muted/30">
                    <span className="font-semibold text-foreground block">Tính cách:</span>
                    <span className="text-muted-foreground">{char.memory.personality}</span>
                  </div>

                  <div className="p-2 rounded bg-muted/30">
                    <span className="font-semibold text-foreground block">Câu cửa miệng:</span>
                    <span className="text-muted-foreground">
                      {char.memory.catchphrases.join(" • ")}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-muted/30">
                    <span className="font-semibold text-foreground block">Thói quen:</span>
                    <span className="text-muted-foreground">
                      {char.memory.habits.join(" • ")}
                    </span>
                  </div>

                  <div className="p-2 rounded bg-muted/30">
                    <span className="font-semibold text-foreground block">Sự kiện đã xảy ra:</span>
                    <span className="text-muted-foreground">
                      {char.memory.pastEventsSummary.join(" • ")}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
