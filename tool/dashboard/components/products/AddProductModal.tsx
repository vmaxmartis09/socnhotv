"use client";

import React, { useState, useEffect } from "react";
import type { Product } from "@/lib/api/intel";
import { intelApi } from "@/lib/api/intel";
import { Globe, Plus, Sparkles, Tag, DollarSign, Package } from "./icons";
import { X, Loader2, Check } from "@/components/ui/icons";

interface AddProductModalProps {
  isOpen: boolean;
  projectId: string;
  initialProduct?: Product | null;
  onClose: () => void;
  onSuccess: (saved: Product) => void;
}

export function AddProductModal({
  isOpen,
  projectId,
  initialProduct,
  onClose,
  onSuccess,
}: AddProductModalProps) {
  const [tab, setTab] = useState<"manual" | "url">("manual");
  const [importUrl, setImportUrl] = useState("");
  const [isImporting, setIsImporting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [category, setCategory] = useState("");
  const [price, setPrice] = useState<number | undefined>(undefined);
  const [salePrice, setSalePrice] = useState<number | undefined>(undefined);
  const [currency, setCurrency] = useState("VND");
  const [image, setImage] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [uspText, setUspText] = useState("");
  const [painPointsText, setPainPointsText] = useState("");
  const [tiktokShop, setTiktokShop] = useState("");
  const [shopee, setShopee] = useState("");
  const [lazada, setLazada] = useState("");
  const [complianceNotes, setComplianceNotes] = useState("");

  useEffect(() => {
    if (initialProduct) {
      setName(initialProduct.name || "");
      setBrand(initialProduct.brand || "");
      setCategory(initialProduct.category || "");
      setPrice(initialProduct.price);
      setSalePrice(initialProduct.sale_price);
      setCurrency(initialProduct.currency || "VND");
      setImage(initialProduct.images?.[0] || "");
      setTargetAudience(initialProduct.target_audience || "");
      setUspText(initialProduct.usp ? initialProduct.usp.join("\n") : "");
      setPainPointsText(initialProduct.pain_points ? initialProduct.pain_points.join("\n") : "");
      setTiktokShop(initialProduct.affiliate_links?.tiktok_shop || "");
      setShopee(initialProduct.affiliate_links?.shopee || "");
      setLazada(initialProduct.affiliate_links?.lazada || "");
      setComplianceNotes(initialProduct.compliance_notes || "");
    } else {
      setName("");
      setBrand("");
      setCategory("");
      setPrice(undefined);
      setSalePrice(undefined);
      setCurrency("VND");
      setImage("");
      setTargetAudience("");
      setUspText("");
      setPainPointsText("");
      setTiktokShop("");
      setShopee("");
      setLazada("");
      setComplianceNotes("");
    }
    setError(null);
  }, [initialProduct, isOpen]);

  if (!isOpen) return null;

  const handleImportUrl = async () => {
    if (!importUrl.trim()) return;
    setIsImporting(true);
    setError(null);
    try {
      const data = await intelApi.importProductFromUrl(projectId, importUrl.trim());
      if (data.name) setName(data.name);
      if (data.brand) setBrand(data.brand);
      if (data.category) setCategory(data.category);
      if (data.price) setPrice(data.price);
      if (data.sale_price) setSalePrice(data.sale_price);
      if (data.currency) setCurrency(data.currency);
      if (data.images && data.images.length > 0) setImage(data.images[0]);
      if (data.usp && data.usp.length > 0) setUspText(data.usp.join("\n"));
      if (data.pain_points && data.pain_points.length > 0)
        setPainPointsText(data.pain_points.join("\n"));
      if (data.target_audience) setTargetAudience(data.target_audience);
      if (data.compliance_notes) setComplianceNotes(data.compliance_notes);
      setTab("manual");
    } catch (err: any) {
      setError(`Lỗi import: ${err.message}`);
    } finally {
      setIsImporting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Vui lòng nhập tên sản phẩm.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const usp = uspText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    const painPoints = painPointsText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);

    const productPayload: Product = {
      id: initialProduct ? initialProduct.id : "",
      name: name.trim(),
      brand: brand.trim() || undefined,
      category: category.trim() || undefined,
      price: price ? Number(price) : undefined,
      sale_price: salePrice ? Number(salePrice) : undefined,
      currency,
      images: image.trim() ? [image.trim()] : [],
      target_audience: targetAudience.trim() || undefined,
      usp,
      pain_points: painPoints,
      affiliate_links: {
        tiktok_shop: tiktokShop.trim() || undefined,
        shopee: shopee.trim() || undefined,
        lazada: lazada.trim() || undefined,
      },
      compliance_notes: complianceNotes.trim() || undefined,
    };

    try {
      let saved: Product;
      if (initialProduct?.id) {
        saved = await intelApi.updateProduct(projectId, initialProduct.id, productPayload);
      } else {
        saved = await intelApi.createProduct(projectId, productPayload);
      }
      onSuccess(saved);
      onClose();
    } catch (err: any) {
      setError(`Lỗi lưu sản phẩm: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div>
            <h2 className="text-lg font-bold text-zinc-100">
              {initialProduct ? "Chỉnh sửa sản phẩm" : "Thêm sản phẩm mới"}
            </h2>
            <p className="text-xs text-zinc-400">
              Khai báo thông tin sản phẩm để tự động tạo kịch bản KOC & video bán hàng
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs if new */}
        {!initialProduct && (
          <div className="mt-3 flex rounded-lg bg-zinc-900 p-1 border border-zinc-800">
            <button
              onClick={() => setTab("manual")}
              className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition ${
                tab === "manual"
                  ? "bg-zinc-800 text-white shadow"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Nhập thủ công
            </button>
            <button
              onClick={() => setTab("url")}
              className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition flex items-center justify-center gap-1.5 ${
                tab === "url"
                  ? "bg-zinc-800 text-white shadow"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Globe className="h-3.5 w-3.5 text-indigo-400" />
              Nhập từ URL (Shopee/TikTok Shop/Web)
            </button>
          </div>
        )}

        {/* URL Import box */}
        {tab === "url" && !initialProduct && (
          <div className="mt-4 rounded-xl border border-indigo-950/60 bg-indigo-950/20 p-4">
            <span className="text-xs font-semibold text-indigo-300">
              Dán URL trang chi tiết sản phẩm:
            </span>
            <div className="mt-2 flex gap-2">
              <input
                type="url"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                placeholder="https://shopee.vn/product/... hoặc https://shop.tiktok.com/..."
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleImportUrl}
                disabled={isImporting || !importUrl.trim()}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {isImporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                Trích xuất
              </button>
            </div>
            <p className="mt-2 text-[11px] text-zinc-400">
              Hệ thống đọc metadata công khai (OpenGraph: tiêu đề, ảnh, mô tả) mà không cần đăng nhập.
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mt-3 rounded-lg border border-rose-900/50 bg-rose-950/30 p-2.5 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-zinc-300">
                Tên sản phẩm <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="VD: Kem chống nắng quang phổ rộng Sóc Nhỏ SunShield"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300">Thương hiệu (Brand)</label>
              <input
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="VD: Sóc Nhỏ Lab"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300">Ngành hàng / Danh mục</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="VD: Mỹ phẩm, Gia dụng, Thời trang"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300">Giá gốc (VNĐ)</label>
              <input
                type="number"
                value={price !== undefined ? price : ""}
                onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="VD: 350000"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300">Giá khuyến mãi (VNĐ)</label>
              <input
                type="number"
                value={salePrice !== undefined ? salePrice : ""}
                onChange={(e) => setSalePrice(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="VD: 289000"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-zinc-300">URL Ảnh sản phẩm</label>
              <input
                type="url"
                value={image}
                onChange={(e) => setImage(e.target.value)}
                placeholder="https://..."
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-zinc-300">Đối tượng mục tiêu</label>
              <input
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="VD: Nữ 18-28 tuổi, da dầu mụn, học sinh sinh viên"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* USP */}
            <div>
              <label className="text-xs font-medium text-emerald-400">
                USP (Mỗi điểm 1 dòng)
              </label>
              <textarea
                rows={3}
                value={uspText}
                onChange={(e) => setUspText(e.target.value)}
                placeholder="Kháng nước 80 phút&#10;Không nâng tone lộ vân kem&#10;Chứa Niacinamide dưỡng sáng"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
              />
            </div>

            {/* Pain Points */}
            <div>
              <label className="text-xs font-medium text-amber-400">
                Nỗi đau khách hàng (Mỗi điểm 1 dòng)
              </label>
              <textarea
                rows={3}
                value={painPointsText}
                onChange={(e) => setPainPointsText(e.target.value)}
                placeholder="Dùng kem bị vón cục, bết dính&#10;Đổ mồ hôi là chảy vệt trắng&#10;Giá các loại cao cấp quá đắt"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-amber-500 focus:outline-none"
              />
            </div>

            {/* Affiliate Links */}
            <div className="sm:col-span-2 space-y-2 pt-2 border-t border-zinc-800">
              <label className="text-xs font-medium text-indigo-400">
                Link Affiliate (Tiếp thị liên kết)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="url"
                  value={tiktokShop}
                  onChange={(e) => setTiktokShop(e.target.value)}
                  placeholder="TikTok Shop URL"
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                />
                <input
                  type="url"
                  value={shopee}
                  onChange={(e) => setShopee(e.target.value)}
                  placeholder="Shopee URL"
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                />
                <input
                  type="url"
                  value={lazada}
                  onChange={(e) => setLazada(e.target.value)}
                  placeholder="Lazada URL"
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Compliance */}
            <div className="sm:col-span-2 pt-2 border-t border-zinc-800">
              <label className="text-xs font-medium text-rose-400">
                Lưu ý Tuân thủ (Cấm nói gì: y tế, cam kết 100%...)
              </label>
              <input
                type="text"
                value={complianceNotes}
                onChange={(e) => setComplianceNotes(e.target.value)}
                placeholder="VD: Không được cam kết trị dứt điểm mụn trong 7 ngày"
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-rose-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="mt-6 flex items-center justify-end gap-2 pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-xs font-semibold text-zinc-300 hover:bg-zinc-800"
            >
              Huỷ
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg hover:bg-indigo-500 disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              {initialProduct ? "Lưu thay đổi" : "Thêm sản phẩm"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
