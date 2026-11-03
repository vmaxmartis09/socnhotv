"use client";

import React, { useRef } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";

/** Thẻ ảnh nghiêng 3D theo con trỏ (kiểu ReactBits TiltedCard), có lớp ánh sáng và chú thích. */
export function TiltedCard({
  src,
  alt,
  caption,
  className,
  max = 12,
  onClick,
}: {
  src: string;
  alt: string;
  caption?: React.ReactNode;
  className?: string;
  max?: number;
  onClick?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const rx = useSpring(useMotionValue(0), { stiffness: 200, damping: 20 });
  const ry = useSpring(useMotionValue(0), { stiffness: 200, damping: 20 });
  const scale = useSpring(useMotionValue(1), { stiffness: 220, damping: 22 });
  const glowX = useMotionValue(50);
  const glowY = useMotionValue(30);

  const move = (e: React.MouseEvent) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    ry.set((px - 0.5) * 2 * max);
    rx.set(-(py - 0.5) * 2 * max);
    glowX.set(px * 100);
    glowY.set(py * 100);
  };
  const leave = () => {
    rx.set(0);
    ry.set(0);
    scale.set(1);
  };

  return (
    <div className={cn("h-full w-full [perspective:900px]", className)}>
      <motion.div
        ref={ref}
        onMouseMove={move}
        onMouseEnter={() => scale.set(1.04)}
        onMouseLeave={leave}
        onClick={onClick}
        style={{ rotateX: rx, rotateY: ry, scale, transformStyle: "preserve-3d" }}
        className="group relative h-full w-full cursor-zoom-in overflow-hidden rounded-[24px] border border-border bg-muted/20"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={alt} className="h-full w-full object-cover object-top" draggable={false} />
        <motion.span
          aria-hidden="true"
          style={{
            background: `radial-gradient(circle at ${"var(--gx)"} ${"var(--gy)"}, rgba(255,255,255,0.35), transparent 55%)`,
          }}
          className="pointer-events-none absolute inset-0 opacity-0 mix-blend-soft-light transition-opacity duration-200 group-hover:opacity-100"
          // gán toạ độ ánh sáng qua biến CSS
          ref={(el) => {
            if (!el) return;
            const ux = glowX.on("change", (v) => el.style.setProperty("--gx", `${v}%`));
            const uy = glowY.on("change", (v) => el.style.setProperty("--gy", `${v}%`));
            (el as any).__off = () => {
              ux();
              uy();
            };
          }}
        />
        {caption && (
          <span className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent px-4 pb-3 pt-10 text-sm font-medium text-white [transform:translateZ(30px)]">
            {caption}
          </span>
        )}
      </motion.div>
    </div>
  );
}
