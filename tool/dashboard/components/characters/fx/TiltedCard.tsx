"use client";

import React, { useRef } from "react";
import { motion, useMotionTemplate, useMotionValue, useSpring } from "framer-motion";
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
  const rectRef = useRef<{ left: number; top: number; width: number; height: number } | null>(null);

  const rx = useSpring(useMotionValue(0), { stiffness: 220, damping: 22 });
  const ry = useSpring(useMotionValue(0), { stiffness: 220, damping: 22 });
  const scale = useSpring(useMotionValue(1), { stiffness: 220, damping: 22 });
  const glowX = useMotionValue(50);
  const glowY = useMotionValue(30);

  const bgGradient = useMotionTemplate`radial-gradient(circle at ${glowX}% ${glowY}%, rgba(255,255,255,0.35), transparent 55%)`;

  const handleMouseEnter = () => {
    if (ref.current) {
      const r = ref.current.getBoundingClientRect();
      rectRef.current = { left: r.left, top: r.top, width: r.width, height: r.height };
    }
    scale.set(1.04);
  };

  const move = (e: React.MouseEvent) => {
    let r = rectRef.current;
    if (!r) {
      const b = ref.current?.getBoundingClientRect();
      if (!b) return;
      r = { left: b.left, top: b.top, width: b.width, height: b.height };
      rectRef.current = r;
    }
    const px = Math.max(0, Math.min(1, (e.clientX - r.left) / (r.width || 1)));
    const py = Math.max(0, Math.min(1, (e.clientY - r.top) / (r.height || 1)));
    ry.set((px - 0.5) * 2 * max);
    rx.set(-(py - 0.5) * 2 * max);
    glowX.set(px * 100);
    glowY.set(py * 100);
  };

  const leave = () => {
    rectRef.current = null;
    rx.set(0);
    ry.set(0);
    scale.set(1);
    glowX.set(50);
    glowY.set(30);
  };

  return (
    <div className={cn("h-full w-full [perspective:900px]", className)}>
      <motion.div
        ref={ref}
        onMouseMove={move}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={leave}
        onClick={onClick}
        style={{
          rotateX: rx,
          rotateY: ry,
          scale,
          transformStyle: "preserve-3d",
          willChange: "transform",
          backfaceVisibility: "hidden",
        }}
        className="group relative h-full w-full cursor-zoom-in overflow-hidden rounded-[24px] border border-border bg-muted/20"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={alt} className="h-full w-full object-cover object-top select-none" draggable={false} />
        <motion.span
          aria-hidden="true"
          style={{ background: bgGradient }}
          className="pointer-events-none absolute inset-0 opacity-0 mix-blend-soft-light transition-opacity duration-200 group-hover:opacity-100"
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
