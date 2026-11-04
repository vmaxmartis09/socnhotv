import { Database, Brain, ShoppingBag } from "./sources-icons";
import type { NavItem } from "./video";

export const sourcesNavItems: NavItem[] = [
  {
    id: "sources",
    href: "/sources",
    labelKey: "sources.title",
    icon: Database,
  },
  {
    id: "products",
    href: "/products",
    labelKey: "products.title",
    icon: ShoppingBag,
  },
  {
    id: "intel",
    href: "/intel",
    labelKey: "intel.title",
    icon: Brain,
  },
];
