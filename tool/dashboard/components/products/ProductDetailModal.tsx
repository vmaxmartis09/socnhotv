"use client";

import React from "react";
import type { Product } from "@/lib/api/intel";
import {
  ShoppingBag,
  Tag,
  DollarSign,
  ExternalLink,
  Edit3,
  Trash2,
  Sparkles,
} from "./icons";
import { X, Check, AlertTriangle } from "@/components/ui/icons";

interface ProductDetailModalProps {
  product: Product | null;
  onClose: () => void;
  onEdit: (p: Product) => void;
  onDelete: (id: string) => void;
  onUseForScript?: (p: Product) => void;
}

export function ProductDetailModal({
  product,
  onClose,
  onEdit,
  onDelete,
  onUseForScript,
}: ProductDetailModalProps) {
  if (!product) return null;

  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return "—";
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: product.currency || "VND",
    }).format(val);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-zinc-800">
          <div>
            <div className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-indigo-400 uppercase tracking-wider">
                {product.brand || "Chưa có thương hiệu"}
              </span>
              {product.category && (
                <span className="rounded-full bg-zinc-800/80 px-2 py-0.5 text-zinc-300">
                  {product.category}
                </span>
              )}
            </div>
            <h2 className="mt-1 text-xl font-bold text-zinc-100">{product.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-4 flex-1 overflow-y-auto pr-1 space-y-6">
          {/* Images & Pricing */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="aspect-video rounded-xl overflow-hidden bg-zinc-900 flex items-center justify-center border border-zinc-800">
              {product.images && product.images[0] ? (
                <img
                  src={product.images[0]}
                  alt={product.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex flex-col items-center gap-2 text-zinc-600">
                  <ShoppingBag className="h-10 w-10" />
                  <span className="text-xs">Chưa có ảnh sản phẩm</span>
                </div>
              )}
            </div>

            <div className="flex flex-col justify-center rounded-xl bg-zinc-900/60 p-4 border border-zinc-800/60">
              <span className="text-xs text-zinc-400">Giá niêm yết & khuyến mãi</span>
              <div className="mt-1 flex items-baseline gap-3">
                <span className="text-2xl font-black text-zinc-100">
                  {formatCurrency(product.sale_price || product.price)}
                </span>
                {product.sale_price && product.price && product.sale_price < product.price && (
                  <span className="text-sm text-zinc-500 line-through">
                    {formatCurrency(product.price)}
                  </span>
                )}
              </div>

              {product.target_audience && (
                <div className="mt-4">
                  <span className="text-xs font-semibold text-zinc-400">Đối tượng mục tiêu:</span>
                  <p className="mt-0.5 text-sm text-zinc-300">{product.target_audience}</p>
                </div>
              )}
            </div>
          </div>

          {/* USP & Pain Points */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* USP */}
            <div className="rounded-xl border border-emerald-950/40 bg-emerald-950/10 p-4">
              <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Check className="h-4 w-4" /> Điểm bán hàng độc nhất (USP)
              </h4>
              <ul className="mt-3 space-y-2">
                {product.usp && product.usp.length > 0 ? (
                  product.usp.map((u, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-200">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
                      <span>{u}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-zinc-500 italic">Chưa liệt kê USP</li>
                )}
              </ul>
            </div>

            {/* Pain Points */}
            <div className="rounded-xl border border-amber-950/40 bg-amber-950/10 p-4">
              <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4" /> Nỗi đau khách hàng giải quyết
              </h4>
              <ul className="mt-3 space-y-2">
                {product.pain_points && product.pain_points.length > 0 ? (
                  product.pain_points.map((p, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-zinc-200">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                      <span>{p}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-zinc-500 italic">Chưa có thông tin</li>
                )}
              </ul>
            </div>
          </div>

          {/* Affiliate Links */}
          {product.affiliate_links && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                <Tag className="h-4 w-4 text-indigo-400" /> Liên kết Tiếp thị liên kết (Affiliate)
              </h4>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(product.affiliate_links).map(([platform, link]) => {
                  if (!link) return null;
                  return (
                    <a
                      key={platform}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-xs text-zinc-300 hover:border-zinc-700 hover:text-white"
                    >
                      <span className="font-semibold capitalize text-indigo-400">
                        {platform.replace("_", " ")}
                      </span>
                      <ExternalLink className="h-3.5 w-3.5 text-zinc-500" />
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {/* Compliance Notes */}
          {product.compliance_notes && (
            <div className="rounded-xl border border-rose-950/50 bg-rose-950/15 p-4">
              <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4" /> Lưu ý Tuân thủ & Quảng cáo
              </h4>
              <p className="mt-2 text-xs text-rose-200/90 leading-relaxed">
                {product.compliance_notes}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 flex items-center justify-between pt-4 border-t border-zinc-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onEdit(product)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-800"
            >
              <Edit3 className="h-3.5 w-3.5" /> Chỉnh sửa
            </button>
            <button
              onClick={() => onDelete(product.id)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-900/40 px-3 py-1.5 text-xs font-medium text-rose-400 hover:bg-rose-950/50"
            >
              <Trash2 className="h-3.5 w-3.5" /> Xoá
            </button>
          </div>

          {onUseForScript && (
            <button
              onClick={() => onUseForScript(product)}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700"
            >
              <Sparkles className="h-4 w-4" /> Tạo Kịch bản Bán hàng
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
