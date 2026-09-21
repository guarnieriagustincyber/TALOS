import React from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";

export interface ClaimStatusBadgeProps {
  status: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "CONTRADICTION" | string;
  groundingRatio?: number;
  claimId?: string;
  hasRedaction?: boolean;
}

export const ClaimStatusBadge: React.FC<ClaimStatusBadgeProps> = ({
  status,
  groundingRatio,
  claimId,
  hasRedaction,
}) => {
  const normalized = status.toUpperCase();

  let badgeStyle = "bg-white/10 text-white/70 border-white/20";
  let icon = <CheckCircle2 className="w-3 h-3" />;
  let label = normalized;

  if (normalized === "SUPPORTED") {
    badgeStyle = "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
    icon = <CheckCircle2 className="w-3 h-3 text-emerald-400" />;
    label = "SUPPORTED";
  } else if (normalized === "PARTIALLY_SUPPORTED" || normalized === "PARTIAL") {
    badgeStyle = "bg-amber-500/10 text-amber-300 border-amber-500/30";
    icon = <AlertTriangle className="w-3 h-3 text-amber-400" />;
    label = "PARTIAL";
  } else if (normalized === "UNSUPPORTED") {
    badgeStyle = "bg-rose-500/10 text-rose-300 border-rose-500/30";
    icon = <AlertCircle className="w-3 h-3 text-rose-400" />;
    label = "UNSUPPORTED";
  } else if (normalized === "CONTRADICTION") {
    badgeStyle = "bg-purple-500/10 text-purple-300 border-purple-500/30";
    icon = <ShieldAlert className="w-3 h-3 text-purple-400" />;
    label = "CONTRADICTION";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[8px] border text-[10px] font-mono font-semibold tracking-wider ${badgeStyle}`}
      title={groundingRatio !== undefined ? `Ratio de grounding: ${(groundingRatio * 100).toFixed(1)}%` : undefined}
    >
      {icon}
      {claimId && <span className="opacity-70 font-mono">{claimId}:</span>}
      <span>{label}</span>
      {groundingRatio !== undefined && (
        <span className="opacity-60 text-[9px]">({(groundingRatio * 100).toFixed(0)}%)</span>
      )}
      {hasRedaction && (
        <span className="ml-1 px-1 py-0.2 rounded bg-rose-950 text-rose-400 text-[8.5px] border border-rose-500/40">
          [SIN_RESPALDO]
        </span>
      )}
    </span>
  );
};

export default ClaimStatusBadge;
