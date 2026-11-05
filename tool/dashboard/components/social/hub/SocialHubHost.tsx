"use client";

import dynamic from "next/dynamic";

export const SocialHubHost = dynamic(
  () => import("./SocialHub").then((m) => m.SocialHub),
  { ssr: false }
);
