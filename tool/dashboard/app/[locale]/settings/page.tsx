"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";
import { useStudioStore } from "@/store";

export default function SettingsRedirectPage() {
  const router = useRouter();
  const { setActiveRightTab } = useStudioStore();

  useEffect(() => {
    setActiveRightTab("chat");
    router.replace("/");
  }, [router, setActiveRightTab]);

  return null;
}
