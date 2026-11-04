"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/routing";

export default function ProductsRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/studio");
  }, [router]);

  return null;
}
