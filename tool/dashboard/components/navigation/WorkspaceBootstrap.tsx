"use client";

import React, { useEffect } from "react";
import { useStudioStore } from "@/store";
import { getRepository } from "@/lib/repositories";
import { checkCoreHealth, fetchNodeTypes } from "@/lib/core-api";

/** Nạp dữ liệu workspace từ Core và gắn phím tắt Ctrl+B; không hiển thị gì. */
export function WorkspaceBootstrap() {
  const {
    activeProjectId,
    setProjects,
    setCharacters,
    setChannels,
    setScheduledPosts,
    toggleRightPanel,
    setNodeCatalog,
    setCoreHealth,
  } = useStudioStore();

  useEffect(() => {
    let active = true;
    async function bootstrapWorkspace() {
      const repo = getRepository();
      const [projs, chars, chans, posts, health, catalog] = await Promise.all([
        repo.listProjects(),
        repo.listCharacters(activeProjectId),
        repo.listChannels(activeProjectId),
        repo.listScheduledPosts(activeProjectId),
        checkCoreHealth(),
        fetchNodeTypes(),
      ]);
      if (!active) return;
      setProjects(projs);
      setCharacters(chars);
      setChannels(chans);
      setScheduledPosts(posts);
      setCoreHealth({ ...health, checkedAt: new Date().toISOString() });
      setNodeCatalog(catalog.definitions, catalog.fromCore);
      if (catalog.fromCore) await useStudioStore.getState().refreshCustomNodeTypes(activeProjectId);
    }
    bootstrapWorkspace();
    return () => {
      active = false;
    };
  }, [
    activeProjectId,
    setProjects,
    setCharacters,
    setChannels,
    setScheduledPosts,
    setCoreHealth,
    setNodeCatalog,
  ]);

  // Keyboard shortcut Ctrl+B to toggle right panel
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggleRightPanel();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleRightPanel]);

  return null;
}
