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
  Image as ImageNode,
  FileText as FileTextNode,
  CheckCircle2 as CheckCircle2Node,
  Clock as ClockNode,
  Zap as ZapNode,
  Bell as BellNode,
  Flame as FlameNode,
  RefreshCw as RefreshCwNode,
  Tag as TagNode,
  MoreVertical as MoreVerticalNode,
  ChevronLeft as ChevronLeftNode,
  Smartphone as SmartphoneNode,
  ArrowUpRight as ArrowUpRightNode,
  AlertCircle as AlertCircleNode,
  Bookmark as BookmarkNode,
  Heart as HeartNode,
  MessageCircle as MessageCircleNode,
  Share2 as Share2Node,
  Filter as FilterNode,
  MoreHorizontal as MoreHorizontalNode,
  CheckCircle as CheckCircleNode,
  XCircle as XCircleNode,
  Grid as GridNode,
  List as ListNode,
  Wrench as WrenchNode,
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
export const Unlink = createMorphIcon(lucide.Unlink, "Unlink");
export const Sliders = createMorphIcon(lucide.Sliders, "Sliders");
export const Maximize2 = createMorphIcon(lucide.Maximize2, "Maximize2");
export const ZoomIn = createMorphIcon(lucide.ZoomIn, "ZoomIn");
export const ZoomOut = createMorphIcon(lucide.ZoomOut, "ZoomOut");
export const ArrowRight = createMorphIcon(lucide.ArrowRight, "ArrowRight");
export const Image = createMorphIcon(lucide.Image, "Image");
export const FileText = createMorphIcon(lucide.FileText, "FileText");
export const CheckCircle2 = createMorphIcon(lucide.CheckCircle2, "CheckCircle2");

// Thanh công cụ Studio & CRUD
export const Trash2 = createMorphIcon(lucide.Trash2, "Trash2");
export const Copy = createMorphIcon(lucide.Copy, "Copy");
export const Pencil = createMorphIcon(lucide.Pencil, "Pencil");
export const MousePointer2 = createMorphIcon(lucide.MousePointer2, "MousePointer2");
export const Hand = createMorphIcon(lucide.Hand, "Hand");
export const Scissors = createMorphIcon(lucide.Scissors, "Scissors");
export const StickyNote = createMorphIcon(lucide.StickyNote, "StickyNote");
export const MessageSquare = createMorphIcon(lucide.MessageSquare, "MessageSquare");
export const Undo2 = createMorphIcon(lucide.Undo2, "Undo2");
export const Redo2 = createMorphIcon(lucide.Redo2, "Redo2");
export const InfinityIcon = createMorphIcon(lucide.Infinity, "Infinity");
export const ClipboardPaste = createMorphIcon(lucide.ClipboardPaste, "ClipboardPaste");
export const X = createMorphIcon(lucide.X, "X");
export const UserPlus = createMorphIcon(lucide.UserPlus, "UserPlus");
export const Link2 = createMorphIcon(lucide.Link2, "Link2");
export const Pin = createMorphIcon(lucide.Pin, "Pin");
export const Square = createMorphIcon(lucide.Square, "Square");
export const ChevronDown = createMorphIcon(lucide.ChevronDown, "ChevronDown");
export const ChevronRight = createMorphIcon(lucide.ChevronRight, "ChevronRight");
export const PanelRightClose = createMorphIcon(lucide.PanelRightClose, "PanelRightClose");
export const PanelRightOpen = createMorphIcon(lucide.PanelRightOpen, "PanelRightOpen");
export const Upload = createMorphIcon(lucide.Upload, "Upload");
export const Search = createMorphIcon(lucide.Search, "Search");
export const Send = createMorphIcon(lucide.Send, "Send");
export const Key = createMorphIcon(lucide.Key, "Key");
export const ListOrdered = createMorphIcon(lucide.ListOrdered, "ListOrdered");
export const AlertTriangle = createMorphIcon(lucide.AlertTriangle, "AlertTriangle");

// Biểu tượng cho node gọn, hub dự án và thanh công cụ
export const Loader2 = createMorphIcon(lucide.Loader2, "Loader2");
export const Circle = createMorphIcon(lucide.Circle, "Circle");
export const CircleDot = createMorphIcon(lucide.CircleDot, "CircleDot");
export const ChevronUp = createMorphIcon(lucide.ChevronUp, "ChevronUp");
export const Mic = createMorphIcon(lucide.Mic, "Mic");
export const ScrollText = createMorphIcon(lucide.ScrollText, "ScrollText");
export const Clapperboard = createMorphIcon(lucide.Clapperboard, "Clapperboard");
export const Images = createMorphIcon(lucide.Images, "Images");
export const Video = createMorphIcon(lucide.Video, "Video");
export const Download = createMorphIcon(lucide.Download, "Download");
export const Wand2 = createMorphIcon(lucide.Wand2, "Wand2");
export const CheckSquare = createMorphIcon(lucide.CheckSquare, "CheckSquare");
export const Hash = createMorphIcon(lucide.Hash, "Hash");
export const Info = createMorphIcon(lucide.Info, "Info");
export const Keyboard = createMorphIcon(lucide.Keyboard, "Keyboard");
export const House = createMorphIcon(lucide.House, "House");
export const Activity = createMorphIcon(lucide.Activity, "Activity");
export const ExternalLink = createMorphIcon(lucide.ExternalLink, "ExternalLink");
export const Bot = createMorphIcon(lucide.Bot, "Bot");
export const ChevronsDown = createMorphIcon(lucide.ChevronsDown, "ChevronsDown");
export const Workflow = createMorphIcon(lucide.Workflow, "Workflow");
export const Pause = createMorphIcon(lucide.Pause, "Pause");
export const AudioLines = createMorphIcon(lucide.AudioLines, "AudioLines");
export const Music = createMorphIcon(lucide.Music, "Music");
export const Headphones = createMorphIcon(lucide.Headphones, "Headphones");
export const VolumeX = createMorphIcon(lucide.VolumeX, "VolumeX");
export const Eye = createMorphIcon(lucide.Eye, "Eye");
export const FolderOpen = createMorphIcon(lucide.FolderOpen, "FolderOpen");
export const FileUp = createMorphIcon(lucide.FileUp, "FileUp");

// Social & Notifications icons
export const Clock = createMorphIcon(lucide.Clock, "Clock");
export const Zap = createMorphIcon(lucide.Zap, "Zap");
export const Bell = createMorphIcon(lucide.Bell, "Bell");
export const Flame = createMorphIcon(lucide.Flame, "Flame");
export const RefreshCw = createMorphIcon(lucide.RefreshCw, "RefreshCw");
export const Tag = createMorphIcon(lucide.Tag, "Tag");
export const MoreVertical = createMorphIcon(lucide.MoreVertical, "MoreVertical");
export const ChevronLeft = createMorphIcon(lucide.ChevronLeft, "ChevronLeft");
export const Smartphone = createMorphIcon(lucide.Smartphone, "Smartphone");
export const ArrowUpRight = createMorphIcon(lucide.ArrowUpRight, "ArrowUpRight");
export const AlertCircle = createMorphIcon(lucide.AlertCircle, "AlertCircle");
export const Bookmark = createMorphIcon(lucide.Bookmark, "Bookmark");
export const Heart = createMorphIcon(lucide.Heart, "Heart");
export const MessageCircle = createMorphIcon(lucide.MessageCircle, "MessageCircle");
export const Share2 = createMorphIcon(lucide.Share2, "Share2");
export const Filter = createMorphIcon(lucide.Filter, "Filter");
export const MoreHorizontal = createMorphIcon(lucide.MoreHorizontal, "MoreHorizontal");
export const CheckCircle = createMorphIcon(lucide.CheckCircle, "CheckCircle");
export const XCircle = createMorphIcon(lucide.XCircle, "XCircle");
export const Grid = createMorphIcon(lucide.Grid, "Grid");
export const List = createMorphIcon(lucide.List, "List");
export const Wrench = createMorphIcon(lucide.Wrench, "Wrench");

