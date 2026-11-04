import { Film } from "@/components/ui/icons";
import type { ComponentType } from "react";

export interface NavItem {
  id: string;
  href: string;
  labelKey: string;
  icon: ComponentType<{ className?: string }>;
}

export const videoNavItems: NavItem[] = [
  {
    id: "templates",
    href: "/templates",
    labelKey: "video.title",
    icon: Film,
  },
];
