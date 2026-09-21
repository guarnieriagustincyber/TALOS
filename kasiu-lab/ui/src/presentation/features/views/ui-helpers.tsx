import React from "react";

export const StatusPill = ({
  children,
  active = false,
  className = "",
}: {
  children: React.ReactNode;
  active?: boolean;
  className?: string;
}) => (
  <span
    className={[
      "inline-flex items-center px-3 py-1.5 rounded-full font-mono text-xs uppercase tracking-wider transition",
      active
        ? "bg-white text-black font-semibold"
        : "bg-white/[0.04] text-white/70 border border-white/[0.08]",
      className,
    ].join(" ")}
  >
    {children}
  </span>
);

export const SectionLabel = ({
  eyebrow,
  title,
}: {
  eyebrow: string;
  title: string;
}) => (
  <div>
    <span className="block text-[10px] md:text-[11px] uppercase tracking-[0.22em] font-mono text-white/35">
      {eyebrow}
    </span>
    <span className="block mt-1 text-xs md:text-sm uppercase tracking-wider font-mono font-semibold text-white">
      {title}
    </span>
  </div>
);

export const Divider = () => <div className="h-px w-full bg-white/[0.07]" />;
