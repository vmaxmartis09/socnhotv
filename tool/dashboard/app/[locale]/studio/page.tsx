"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";

export default function StudioRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/");
  }, [router]);

  return null;
}
