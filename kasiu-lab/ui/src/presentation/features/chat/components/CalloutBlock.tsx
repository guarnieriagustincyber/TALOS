import React from "react";
import {
  Info,
  Lightbulb,
  AlertTriangle,
  ShieldAlert,
  Bookmark,
  Quote,
} from "lucide-react";

export interface CalloutBlockProps {
  children?: React.ReactNode;
}

type CalloutType = "note" | "tip" | "important" | "warning" | "caution" | "quote";

interface CalloutConfig {
  type: CalloutType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  borderClass: string;
  bgClass: string;
  textClass: string;
  badgeClass: string;
}

const CALLOUT_CONFIGS: Record<CalloutType, CalloutConfig> = {
  note: {
    type: "note",
    label: "NOTA TÉCNICA",
    icon: Info,
    borderClass: "border-sky-500/35",
    bgClass: "bg-sky-950/15",
    textClass: "text-sky-300",
    badgeClass: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  },
  tip: {
    type: "tip",
    label: "CONSEJO PEDAGÓGICO",
    icon: Lightbulb,
    borderClass: "border-emerald-500/35",
    bgClass: "bg-emerald-950/15",
    textClass: "text-emerald-300",
    badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  },
  important: {
    type: "important",
    label: "REQUISITO CLAVE",
    icon: Bookmark,
    borderClass: "border-purple-500/35",
    bgClass: "bg-purple-950/15",
    textClass: "text-purple-300",
    badgeClass: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  },
  warning: {
    type: "warning",
    label: "ADVERTENCIA DE PROTOCOLO",
    icon: AlertTriangle,
    borderClass: "border-amber-500/35",
    bgClass: "bg-amber-950/15",
    textClass: "text-amber-300",
    badgeClass: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  },
  caution: {
    type: "caution",
    label: "ALERTA CRÍTICA",
    icon: ShieldAlert,
    borderClass: "border-rose-500/35",
    bgClass: "bg-rose-950/15",
    textClass: "text-rose-300",
    badgeClass: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  },
  quote: {
    type: "quote",
    label: "CITA CANÓNICA",
    icon: Quote,
    borderClass: "border-emerald-500/30",
    bgClass: "bg-white/[0.02]",
    textClass: "text-white/80",
    badgeClass: "bg-white/[0.06] text-white/70 border-white/[0.1]",
  },
};

// Extrae el texto inicial para detectar marcadores de admonition [!NOTE], etc.
const extractCalloutType = (
  children: React.ReactNode
): { type: CalloutType; content: React.ReactNode } => {
  if (!children) return { type: "quote", content: children };

  // Analizar si el primer hijo es un párrafo o string que contiene [!TYPE]
  let detectedType: CalloutType = "quote";
  let strippedChildren = children;

  const inspectText = (text: string): CalloutType | null => {
    const match = text.match(/^\s*\[!(NOTE|INFO|TIP|SUGGESTION|IMPORTANT|WARNING|CAUTION)\]\s*/i);
    if (!match) return null;
    const tag = match[1].toUpperCase();
    if (["NOTE", "INFO"].includes(tag)) return "note";
    if (["TIP", "SUGGESTION"].includes(tag)) return "tip";
    if (["IMPORTANT"].includes(tag)) return "important";
    if (["WARNING"].includes(tag)) return "warning";
    if (["CAUTION"].includes(tag)) return "caution";
    return null;
  };

  if (typeof children === "string") {
    const t = inspectText(children);
    if (t) {
      detectedType = t;
      strippedChildren = children.replace(/^\s*\[!(NOTE|INFO|TIP|SUGGESTION|IMPORTANT|WARNING|CAUTION)\]\s*/i, "");
    }
  } else if (React.isValidElement(children)) {
    const pProps = children.props as { children?: React.ReactNode };
    if (pProps && typeof pProps.children === "string") {
      const t = inspectText(pProps.children);
      if (t) {
        detectedType = t;
        strippedChildren = React.cloneElement(
          children,
          {},
          pProps.children.replace(/^\s*\[!(NOTE|INFO|TIP|SUGGESTION|IMPORTANT|WARNING|CAUTION)\]\s*/i, "")
        );
      }
    } else if (pProps && Array.isArray(pProps.children) && typeof pProps.children[0] === "string") {
      const firstStr = pProps.children[0];
      const t = inspectText(firstStr);
      if (t) {
        detectedType = t;
        const newFirst = firstStr.replace(/^\s*\[!(NOTE|INFO|TIP|SUGGESTION|IMPORTANT|WARNING|CAUTION)\]\s*/i, "");
        strippedChildren = React.cloneElement(children, {}, [
          newFirst,
          ...pProps.children.slice(1),
        ]);
      }
    }
  } else if (Array.isArray(children) && children.length > 0) {
    const first = children[0];
    if (React.isValidElement(first)) {
      const res = extractCalloutType(first);
      if (res.type !== "quote") {
        detectedType = res.type;
        strippedChildren = [res.content, ...children.slice(1)];
      }
    }
  }

  return { type: detectedType, content: strippedChildren };
};

export const CalloutBlock: React.FC<CalloutBlockProps> = ({ children }) => {
  const { type, content } = extractCalloutType(children);
  const cfg = CALLOUT_CONFIGS[type];
  const Icon = cfg.icon;

  return (
    <div
      className={`my-4 p-3.5 sm:p-4 rounded-[14px] border ${cfg.borderClass} ${cfg.bgClass} backdrop-blur-xs relative overflow-hidden transition-all shadow-md group`}
    >
      {/* Barra superior de Admonition */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.05] select-none">
        <div className="flex items-center gap-2">
          <Icon className={`w-3.5 h-3.5 shrink-0 ${cfg.textClass}`} />
          <span className={`px-2 py-0.5 rounded text-[9.5px] font-bold tracking-wider font-mono border ${cfg.badgeClass}`}>
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Contenido */}
      <div className="text-[14px] md:text-[15px] leading-relaxed text-neutral-200/90 font-sans italic space-y-2 [&>p]:my-1">
        {content}
      </div>
    </div>
  );
};

export default CalloutBlock;
