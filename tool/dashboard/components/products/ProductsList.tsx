"use client";

import React, { useState, useEffect, useMemo } from "react";
import type { Product } from "@/lib/api/intel";
import { intelApi } from "@/lib/api/intel";
import { ProductCard } from "./ProductCard";
import { ProductDetailModal } from "./ProductDetailModal";
import { AddProductModal } from "./AddProductModal";
import { ShoppingBag, Plus, Tag } from "./icons";
import { Search, Loader2 } from "@/components/ui/icons";
import { useRouter } from "next/navigation";

interface ProductsListProps {
  projectId: string;
}

export function ProductsList({ projectId }: ProductsListProps) {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isAddOpen, setIsAddOpen] = useState(false);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await intelApi.fetchProducts(projectId);
      setProducts(data);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [projectId]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    products.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set);
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchSearch =
        search === "" ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.brand?.toLowerCase().includes(search.toLowerCase()) ||
        p.usp?.some((u) => u.toLowerCase().includes(search.toLowerCase()));

      const matchCategory =
        selectedCategory === "all" || p.category === selectedCategory;

      return matchSearch && matchCategory;
    });
  }, [products, search, selectedCategory]);

  const handleDelete = async (id: string) => {
    if (!confirm("Bạn có chắc muốn chuyển sản phẩm này vào thùng rác?")) return;
    try {
      await intelApi.deleteProduct(projectId, id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
      if (selectedProduct?.id === id) setSelectedProduct(null);
    } catch (err: any) {
      alert(`Lỗi xoá: ${err.message}`);
    }
  };

  const handleUseForScript = (product: Product) => {
    // Navigate to intel page with preselected product
    router.push(`/intel?productId=${product.id}`);
  };

  return (
    <div className="space-y-6">
      {/* Controls & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo tên sản phẩm, thương hiệu, USP..."
            className="w-full rounded-xl border border-zinc-800 bg-zinc-950/80 pl-9 pr-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        {/* Action button */}
        <button
          onClick={() => {
            setEditingProduct(null);
            setIsAddOpen(true);
          }}
          className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/25 hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Thêm sản phẩm
        </button>
      </div>

      {/* Category Pills */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory("all")}
            className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
              selectedCategory === "all"
                ? "bg-indigo-600 text-white"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Tất cả ({products.length})
          </button>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setSelectedCategory(c)}
              className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                selectedCategory === c
                  ? "bg-indigo-600 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="flex h-64 items-center justify-center text-zinc-500">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
          <span className="ml-2 text-xs">Đang tải danh mục sản phẩm...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredProducts.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              onSelect={setSelectedProduct}
              onEdit={(prod) => {
                setEditingProduct(prod);
                setIsAddOpen(true);
              }}
              onDelete={handleDelete}
            />
          ))}

          {/* Dashed Add Card at the end */}
          <div
            onClick={() => {
              setEditingProduct(null);
              setIsAddOpen(true);
            }}
            className="flex min-h-[260px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-zinc-800 bg-zinc-950/30 p-6 text-center transition-all duration-200 hover:border-indigo-500/60 hover:bg-zinc-900/40 cursor-pointer group"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-900 text-zinc-400 group-hover:bg-indigo-600 group-hover:text-white transition">
              <Plus className="h-6 w-6" />
            </div>
            <h4 className="mt-3 text-sm font-semibold text-zinc-300 group-hover:text-white">
              Thêm sản phẩm mới
            </h4>
            <p className="mt-1 text-xs text-zinc-500">
              Nhập tay hoặc bóc tách từ link Shopee/TikTok Shop
            </p>
          </div>
        </div>
      )}

      {/* Modals */}
      <ProductDetailModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onEdit={(p) => {
          setSelectedProduct(null);
          setEditingProduct(p);
          setIsAddOpen(true);
        }}
        onDelete={handleDelete}
        onUseForScript={handleUseForScript}
      />

      <AddProductModal
        isOpen={isAddOpen}
        projectId={projectId}
        initialProduct={editingProduct}
        onClose={() => {
          setIsAddOpen(false);
          setEditingProduct(null);
        }}
        onSuccess={() => {
          loadProducts();
        }}
      />
    </div>
  );
}
