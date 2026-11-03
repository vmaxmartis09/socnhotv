"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { getRepository, type Project } from "@/lib/repositories";
import { useStudioStore } from "@/store";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { FolderGit2, Plus, Users, Film, Check, Calendar } from "@/components/ui/icons";

export default function ProjectsPage() {
  const t = useTranslations();
  const { activeProjectId, setActiveProjectId, setProjects } = useStudioStore();
  const [list, setList] = useState<Project[]>([]);

  useEffect(() => {
    async function load() {
      const repo = getRepository();
      const projects = await repo.listProjects();
      setList(projects);
      setProjects(projects);
    }
    load();
  }, [setProjects]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-foreground">
            {t("workspace.allProjects")}
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Mỗi dự án có tài nguyên, nhân vật và kịch bản hoàn toàn độc lập trong data/projects/
          </p>
        </div>

        <Button size="md">
          <Plus className="w-4 h-4 mr-1.5" />
          <span>{t("workspace.newProject")}</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((proj) => {
          const isActive = proj.id === activeProjectId;

          return (
            <Card
              key={proj.id}
              className={`transition-all duration-200 ${
                isActive
                  ? "border-primary ring-1 ring-primary/40 shadow-float"
                  : "hover:border-primary/40"
              }`}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <span className="p-2 rounded-md bg-primary/10 text-primary">
                    <FolderGit2 className="w-4 h-4" />
                  </span>
                  {isActive && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-semantic-success/15 text-semantic-success text-[10px] font-semibold">
                      <Check className="w-3 h-3" />
                      Active
                    </span>
                  )}
                </div>
                <CardTitle className="text-base mt-2">{proj.name}</CardTitle>
                <CardDescription className="line-clamp-2 mt-1">
                  {proj.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-2 text-xs">
                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-primary" />
                    Nhân vật:
                  </span>
                  <span className="font-semibold text-foreground">
                    {proj.charactersCount}
                  </span>
                </div>

                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Film className="w-3.5 h-3.5 text-primary" />
                    Tập phim:
                  </span>
                  <span className="font-semibold text-foreground">
                    {proj.episodesCount}
                  </span>
                </div>

                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    Tỉ lệ mặc định:
                  </span>
                  <span className="font-mono text-foreground font-medium">
                    {proj.defaultAspectRatio}
                  </span>
                </div>
              </CardContent>

              <CardFooter className="pt-2">
                {!isActive ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => setActiveProjectId(proj.id)}
                  >
                    Chọn dự án này
                  </Button>
                ) : (
                  <Button variant="secondary" size="sm" className="w-full" disabled>
                    Đang chọn
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
