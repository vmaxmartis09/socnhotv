import { videoNavItems, type NavItem } from "./video";
import { sourcesNavItems } from "./sources";
import { socialNavItems } from "./social";

export type { NavItem };

export const allNavItems: NavItem[] = [
  ...videoNavItems,
  ...sourcesNavItems,
  ...socialNavItems,
];
