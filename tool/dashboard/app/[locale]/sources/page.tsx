"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";

export default function SourcesRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/studio");
  }, [router]);

  return null;
}
