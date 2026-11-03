"use client";

import * as lucide from "lucide";
import { createMorphIcon } from "./MorphIcon";

export { MorphIcon, createMorphIcon } from "./MorphIcon";
export type { MorphIconProps, MorphHandle, IconNode } from "./MorphIcon";

// Raw icon data nodes (IconNode) for dynamic morphing via <MorphIcon icon={...} />
export {
  Sun as SunNode,
  Moon as MoonNode,
  Laptop as LaptopNode,
  LayoutDashboard as LayoutDashboardNode,
  Film as FilmNode,
  FolderGit2 as FolderGit2Node,
  Users2 as Users2Node,
  CalendarDays as CalendarDaysNode,
  Settings as SettingsNode,
  Plus as PlusNode,
  Sparkles as SparklesNode,
  Ruler as RulerNode,
  Volume2 as Volume2Node,
  Brain as BrainNode,
  Users as UsersNode,
  Check as CheckNode,
  Calendar as CalendarNode,
  Globe as GlobeNode,
  Database as DatabaseNode,
  ShieldCheck as ShieldCheckNode,
  DollarSign as DollarSignNode,
  Play as PlayNode,
  RotateCcw as RotateCcwNode,
  Layers as LayersNode,
  Sliders as SlidersNode,
  Maximize2 as Maximize2Node,
  ZoomIn as ZoomInNode,
  ZoomOut as ZoomOutNode,
  ArrowRight as ArrowRightNode,
} from "lucide";

// Universal morphing icon components powered by morphicons.com
export const Sun = createMorphIcon(lucide.Sun, "Sun");
export const Moon = createMorphIcon(lucide.Moon, "Moon");
export const Laptop = createMorphIcon(lucide.Laptop, "Laptop");
export const LayoutDashboard = createMorphIcon(lucide.LayoutDashboard, "LayoutDashboard");
export const Film = createMorphIcon(lucide.Film, "Film");
export const FolderGit2 = createMorphIcon(lucide.FolderGit2, "FolderGit2");
export const Users2 = createMorphIcon(lucide.Users2, "Users2");
export const CalendarDays = createMorphIcon(lucide.CalendarDays, "CalendarDays");
export const Settings = createMorphIcon(lucide.Settings, "Settings");
export const Plus = createMorphIcon(lucide.Plus, "Plus");
export const Sparkles = createMorphIcon(lucide.Sparkles, "Sparkles");
export const Ruler = createMorphIcon(lucide.Ruler, "Ruler");
export const Volume2 = createMorphIcon(lucide.Volume2, "Volume2");
export const Brain = createMorphIcon(lucide.Brain, "Brain");
export const Users = createMorphIcon(lucide.Users, "Users");
export const Check = createMorphIcon(lucide.Check, "Check");
export const Calendar = createMorphIcon(lucide.Calendar, "Calendar");
export const Globe = createMorphIcon(lucide.Globe, "Globe");
export const Database = createMorphIcon(lucide.Database, "Database");
export const ShieldCheck = createMorphIcon(lucide.ShieldCheck, "ShieldCheck");
export const DollarSign = createMorphIcon(lucide.DollarSign, "DollarSign");
export const Play = createMorphIcon(lucide.Play, "Play");
export const RotateCcw = createMorphIcon(lucide.RotateCcw, "RotateCcw");
export const Layers = createMorphIcon(lucide.Layers, "Layers");
export const Sliders = createMorphIcon(lucide.Sliders, "Sliders");
export const Maximize2 = createMorphIcon(lucide.Maximize2, "Maximize2");
export const ZoomIn = createMorphIcon(lucide.ZoomIn, "ZoomIn");
export const ZoomOut = createMorphIcon(lucide.ZoomOut, "ZoomOut");
export const ArrowRight = createMorphIcon(lucide.ArrowRight, "ArrowRight");
