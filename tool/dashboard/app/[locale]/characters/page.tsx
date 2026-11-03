"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";
import { useStudioStore } from "@/store";

export default function CharactersRedirectPage() {
  const router = useRouter();
  const { setActiveRightTab, setRightPanelCollapsed } = useStudioStore();

  useEffect(() => {
    setActiveRightTab("project");
    setRightPanelCollapsed(false);
    router.replace("/");
  }, [router, setActiveRightTab, setRightPanelCollapsed]);

  return null;
}
