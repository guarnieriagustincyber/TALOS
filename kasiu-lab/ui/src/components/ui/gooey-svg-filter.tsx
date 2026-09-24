"use client";

import React from "react";

export interface GooeySvgFilterProps {
  id?: string;
  strength?: number;
  className?: string;
}

export const GooeySvgFilter: React.FC<GooeySvgFilterProps> = ({
  id = "gooey-filter",
  strength = 12,
  className,
}) => {
  return (
    <svg
      className={`absolute w-0 h-0 pointer-events-none opacity-0 overflow-hidden ${className || ""}`}
      aria-hidden="true"
    >
      <defs>
        <filter id={id} colorInterpolationFilters="sRGB">
          <feGaussianBlur
            in="SourceGraphic"
            stdDeviation={strength}
            result="blur"
          />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values={`1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 ${strength * 2.2} -${strength * 1.1}`}
            result="gooey"
          />
          <feComposite in="SourceGraphic" in2="gooey" operator="atop" />
        </filter>
      </defs>
    </svg>
  );
};

export default GooeySvgFilter;
