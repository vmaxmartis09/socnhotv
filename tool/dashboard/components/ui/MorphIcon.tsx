"use client";

import React, { forwardRef } from "react";
import {
  MorphIcon as BaseMorphIcon,
  type MorphIconProps as BaseMorphIconProps,
  type MorphHandle,
} from "morphicons/react";
import type { IconNode } from "lucide";

export type { MorphHandle, IconNode };

export interface MorphIconProps extends Omit<BaseMorphIconProps, "icon"> {
  /** IconNode from 'lucide' or SVG path string */
  icon?: IconNode | string;
}

/**
 * MorphIcon - Universal morphing SVG icon powered by morphicons.com
 * Supports smooth spring-physics morphing between any two icons.
 */
export const MorphIcon = forwardRef<MorphHandle, MorphIconProps>(function MorphIcon(
  { spring = "snappy", strokeWidth = 1.5, size, className, ...props },
  ref
) {
  return (
    <BaseMorphIcon
      ref={ref}
      spring={spring}
      strokeWidth={strokeWidth}
      size={size}
      className={className}
      {...props}
    />
  );
});

MorphIcon.displayName = "MorphIcon";

export interface StaticMorphIconProps extends Omit<MorphIconProps, "icon"> {}

/**
 * Factory to create a pre-configured MorphIcon component for drop-in usage
 */
export function createMorphIcon(node: IconNode, displayName?: string) {
  const Component = forwardRef<MorphHandle, StaticMorphIconProps>((props, ref) => (
    <MorphIcon ref={ref} icon={node} {...props} />
  ));
  if (displayName) {
    Component.displayName = displayName;
  }
  return Component;
}
