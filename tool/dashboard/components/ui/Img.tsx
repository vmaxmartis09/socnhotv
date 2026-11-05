"use client";

import React, { useState, forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface ImgProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  fallbackSrc?: string;
  showSkeleton?: boolean;
}

/**
 * Component Img tối ưu hóa cho AI Video Studio:
 * - Mặc định loading="lazy", decoding="async"
 * - Hiệu ứng skeleton mờ nhẹ khi đang tải
 * - Tự động fallback khi ảnh lỗi hoặc URL không tồn tại
 * - Tuân thủ quy chuẩn hiệu năng UI
 */
export const Img = forwardRef<HTMLImageElement, ImgProps>(function Img(
  {
    src,
    alt = "",
    loading = "lazy",
    decoding = "async",
    className,
    fallbackSrc,
    showSkeleton = false,
    onLoad,
    onError,
    ...props
  },
  ref
) {
  const [loaded, setLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const displaySrc = hasError && fallbackSrc ? fallbackSrc : src;

  return (
    <span className={cn("relative inline-block overflow-hidden", className)}>
      {!loaded && !hasError && showSkeleton && (
        <span
          aria-hidden="true"
          className="absolute inset-0 z-0 animate-pulse bg-muted/40"
        />
      )}
      <img
        ref={ref}
        src={displaySrc}
        alt={alt}
        loading={loading}
        decoding={decoding}
        onLoad={(e) => {
          setLoaded(true);
          onLoad?.(e);
        }}
        onError={(e) => {
          setHasError(true);
          onError?.(e);
        }}
        className={cn(
          "h-full w-full object-cover transition-opacity duration-200",
          showSkeleton && !loaded && "opacity-0",
          className
        )}
        {...props}
      />
    </span>
  );
});
