import React from "react";

/** Acorn mark: Sóc Nhỏ's food, drawn in the brand chestnut. */
export function Mark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className}
      fill="none"
    >
      <path
        d="M12 3.2c-1.1 0-1.9.7-2.1 1.6C6.6 5.500 4.500 8 4.500 10.500h15c0-2.500-2.100-5-5.400-5.700-.2-.9-1-1.600-2.100-1.600Z"
        fill="hsl(var(--brand))"
      />
      <path
        d="M5.500 12.500h13c-.4 4.300-2.900 7.500-6.500 8.300-3.600-.8-6.100-4-6.500-8.300Z"
        fill="hsl(var(--brand))"
        opacity="0.55"
      />
    </svg>
  );
}
