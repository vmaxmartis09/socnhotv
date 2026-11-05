"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";
import { useStudioStore } from "@/store";

/** Studio là màn duy nhất: mở panel tương ứng rồi quay về canvas. */
export default function ProjectsRedirectPage() {
  const router = useRouter();
  const setActiveRightTab = useStudioStore((s) => s.setActiveRightTab);

  useEffect(() => {
    setActiveRightTab("project");
    router.replace("/");
  }, [router, setActiveRightTab]);

  return null;
}
