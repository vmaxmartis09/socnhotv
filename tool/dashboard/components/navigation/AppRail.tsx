"use client";

import { enterOnce } from "@/lib/motion";
import React from "react";
import { motion } from "framer-motion";
import { UserBubble } from "./UserBubble";

/** Chỉ còn hồ sơ (sticky góc dưới trái). Về Sảnh: bấm icon nhà ở breadcrumb; công việc: dock bên phải. */
export function AppRail() {
  return (
    <motion.div
      initial={enterOnce("appbubble", { opacity: 0, scale: 0.9 })}
      animate={{ opacity: 1, scale: 1 }}
      className="pointer-events-auto absolute bottom-3 left-3 z-40 hidden md:block"
    >
      <UserBubble compact placement="beside" />
    </motion.div>
  );
}
