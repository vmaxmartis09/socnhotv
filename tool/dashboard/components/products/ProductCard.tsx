"use client";

import React from "react";
import type { Product } from "@/lib/api/intel";
import { ShoppingBag, Tag, Trash2, Edit3, ExternalLink } from "./icons";

interface ProductCardProps {
  product: Product;
  onSelect: (p: Product) => void;
  onEdit: (p: Product) => void;
  onDelete: (id: string) => void;
}

export function ProductCard({ product, onSelect, onEdit, onDelete }: ProductCardProps) {
  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return "—";
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: product.currency || "VND",
    }).format(val);
  };

  const hasAffiliate =
    product.affiliate_links &&
    Object.values(product.affiliate_links).some((v) => Boolean(v));

  const mainImage = product.images?.[0];

  return (
    <div
      onClick={() => onSelect(product)}
      className="group relative flex flex-col overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/70 p-4 transition-all duration-200 hover:border-zinc-700 hover:bg-zinc-900/50 hover:shadow-lg cursor-pointer"
    >
      {/* Thumbnail */}
      <div className="relative mb-3 flex aspect-video w-full items-center justify-center overflow-hidden rounded-lg bg-zinc-900">
        {mainImage ? (
          <img
            src={mainImage}
            alt={product.name}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex flex-col items-center gap-1 text-zinc-600">
            <ShoppingBag className="h-8 w-8" />
            <span className="text-xs">Chưa có ảnh</span>
          </div>
        )}

        {product.sale_price && product.price && product.sale_price < product.price && (
          <span className="absolute left-2 top-2 rounded-md bg-rose-500/90 px-2 py-0.5 text-xs font-semibold text-white shadow">
            Giảm {Math.round(((product.price - product.sale_price) / product.price) * 100)}%
          </span>
        )}

        {hasAffiliate && (
          <span className="absolute right-2 top-2 flex items-center gap-1 rounded-md bg-emerald-500/20 px-2 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/30">
            <Tag className="h-3 w-3" />
            Affiliate
          </span>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="font-medium text-indigo-400">{product.brand || "Brand"}</span>
            {product.category && <span>• {product.category}</span>}
          </div>
          <h3 className="mt-1 line-clamp-2 text-sm font-semibold text-zinc-100 group-hover:text-indigo-300">
            {product.name}
          </h3>
        </div>

        {/* Pricing & Badges */}
        <div className="mt-4 pt-3 border-t border-zinc-800/60 flex items-center justify-between">
          <div>
            <div className="text-base font-bold text-zinc-100">
              {formatCurrency(product.sale_price || product.price)}
            </div>
            {product.sale_price && product.price && product.sale_price < product.price && (
              <div className="text-xs text-zinc-500 line-through">
                {formatCurrency(product.price)}
              </div>
            )}
          </div>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit(product);
              }}
              title="Chỉnh sửa"
              className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            >
              <Edit3 className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(product.id);
              }}
              title="Xoá"
              className="p-1.5 rounded-md hover:bg-rose-950/50 text-zinc-400 hover:text-rose-400"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
