"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { PageBar } from "@/components/studio/PageBar";
import { ShoppingBag } from "@/components/products/icons";
import { useStudioStore } from "@/store";
import { ProductsList } from "@/components/products/ProductsList";

export default function ProductsPage() {
  const t = useTranslations("products");
  const { activeProjectId } = useStudioStore();

  return (
    <div className="relative h-full w-full overflow-clip">
      <PageBar page="products" />
      <div className="scroll-quiet h-full overflow-y-auto">
        <div className="mx-auto max-w-[1200px] space-y-6 px-6 pb-12 pt-16 md:pr-16">
          {/* Header */}
          <div className="flex flex-col gap-1">
            <h1 className="flex items-center gap-2 text-lg font-bold text-foreground">
              <ShoppingBag className="h-5 w-5 text-indigo-400" />
              {t("title")}
            </h1>
            <p className="text-xs text-muted-foreground">{t("description")}</p>
          </div>

          {/* Product Grid */}
          <ProductsList projectId={activeProjectId || "soc-nho-tv"} />
        </div>
      </div>
    </div>
  );
}
