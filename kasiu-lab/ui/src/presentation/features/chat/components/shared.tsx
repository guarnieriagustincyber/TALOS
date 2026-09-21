import {
  Terminal,
  Shield,
  Network,
  Cpu,
  Lock,
  Database,
  Binary,
  BookOpen,
  FolderOpen,
  Folder,
  FileText,
} from "lucide-react";

export const SYSTEM_NAME = "TALOS";

export const THEME_COLORS: Record<string, { text: string; bg: string; border: string; glow: string; dot: string }> = {
  amber: { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", glow: "shadow-[0_0_12px_rgba(245,158,11,0.2)]", dot: "bg-amber-400" },
  emerald: { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", glow: "shadow-[0_0_12px_rgba(16,185,129,0.2)]", dot: "bg-emerald-400" },
  purple: { text: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/30", glow: "shadow-[0_0_12px_rgba(168,85,247,0.2)]", dot: "bg-purple-400" },
  blue: { text: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/30", glow: "shadow-[0_0_12px_rgba(56,189,248,0.2)]", dot: "bg-sky-400" },
  rose: { text: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/30", glow: "shadow-[0_0_12px_rgba(244,63,94,0.2)]", dot: "bg-rose-400" },
  zinc: { text: "text-zinc-300", bg: "bg-white/[0.06]", border: "border-white/20", glow: "shadow-[0_0_12px_rgba(255,255,255,0.15)]", dot: "bg-white" },
};

export const renderItemIcon = (iconName?: string, isFolder?: boolean, isExpanded?: boolean, className = "w-4 h-4 shrink-0") => {
  switch (iconName) {
    case "terminal": return <Terminal className={className} />;
    case "shield": return <Shield className={className} />;
    case "network": return <Network className={className} />;
    case "cpu": return <Cpu className={className} />;
    case "lock": return <Lock className={className} />;
    case "database": return <Database className={className} />;
    case "binary": return <Binary className={className} />;
    case "book": return <BookOpen className={className} />;
    default:
      if (isFolder) {
        return isExpanded ? <FolderOpen className={className} /> : <Folder className={className} />;
      }
      return <FileText className={className} />;
  }
};
