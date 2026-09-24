import React from "react";
import { AnimatePresence, motion } from "motion/react";
import type { Variants } from "motion/react";

export type PresetType = "blur" | "fade-in-blur" | "scale" | "fade" | "slide";
export type PerType = "word" | "line";

export interface TextEffectProps {
  children: string;
  per?: PerType;
  as?: keyof React.JSX.IntrinsicElements;
  className?: string;
  preset?: PresetType;
  delay?: number;
  speedReveal?: number;
  trigger?: boolean;
  onAnimationComplete?: () => void;
  style?: React.CSSProperties;
}

const presetVariants: Record<PresetType, Variants> = {
  blur: {
    hidden: { opacity: 0, filter: "blur(8px)" },
    visible: { opacity: 1, filter: "blur(0px)", transition: { duration: 0.25 } },
    exit: { opacity: 0, filter: "blur(8px)" },
  },
  "fade-in-blur": {
    hidden: { opacity: 0, y: 6, filter: "blur(8px)" },
    visible: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.28, ease: "easeOut" } },
    exit: { opacity: 0, y: 6, filter: "blur(8px)" },
  },
  fade: {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.2 } },
    exit: { opacity: 0 },
  },
  slide: {
    hidden: { opacity: 0, y: 8 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } },
    exit: { opacity: 0, y: 8 },
  },
  scale: {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.2 } },
    exit: { opacity: 0, scale: 0.95 },
  },
};

export const TextEffect: React.FC<TextEffectProps> = ({
  children,
  per = "word",
  as = "p",
  className = "",
  preset = "fade-in-blur",
  delay = 0,
  speedReveal = 1,
  trigger = true,
  onAnimationComplete,
  style,
}) => {
  if (!children || typeof children !== "string") {
    return <span className={className}>{children}</span>;
  }

  const segments = per === "line" ? children.split("\n") : children.split(/(\s+)/);
  const MotionTag = (motion as any)[as] || motion.p;

  const itemVariants = presetVariants[preset] || presetVariants["fade-in-blur"];
  const stagger = (per === "line" ? 0.08 : 0.035) / speedReveal;

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: stagger,
        delayChildren: delay,
      },
    },
    exit: {
      opacity: 0,
    },
  };

  return (
    <AnimatePresence mode="popLayout">
      {trigger && (
        <MotionTag
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={containerVariants}
          className={className}
          onAnimationComplete={onAnimationComplete}
          style={style}
        >
          {per !== "line" && <span className="sr-only">{children}</span>}
          {segments.map((segment, index) => {
            if (/^\s+$/.test(segment)) {
              return (
                <span key={`space-${index}`} className="inline">
                  {segment}
                </span>
              );
            }
            return (
              <motion.span
                key={`seg-${index}-${segment}`}
                aria-hidden="true"
                variants={itemVariants}
                className="inline-block"
              >
                {segment}
              </motion.span>
            );
          })}
        </MotionTag>
      )}
    </AnimatePresence>
  );
};
