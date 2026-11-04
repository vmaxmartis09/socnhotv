"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";

export default function PublishRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/social");
  }, [router]);

  return null;
}
